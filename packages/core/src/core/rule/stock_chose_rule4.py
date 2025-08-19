from core.rule.base import Rule
import pandas as pd
import numpy as np
import datetime
from copy import deepcopy
import os
import akshare as ak
from core.logger import log
from sqlalchemy.orm import Session
from core.models._stock import StockHistoryDB
from core.database import get_db_session, get_hist_db_session
from core.logger import log
import concurrent.futures


def stock_chose_rule4():
    """
    选股规则4：取月柱的最高点，近三个月 && 当日收盘价，比月柱的最高价，回调了30%～40%
    """
    log.info("开始执行选股规则4")
    try:
        rule4 = Rule4()
        filter_stock_info = rule4.chose()
        if filter_stock_info.empty:
            log.info("没有符合规则4的股票")
        else:
            log.info(f"符合规则4的股票数量: {len(filter_stock_info)}")
            stock_list = filter_stock_info["symbol"].tolist()
            log.info(
                f"本次筛选共找到{len(stock_list)}只符合条件的股票："
                + ", ".join(stock_list)
            )
            # 保存结果到数据库
            from core.models._rule import StockChoseDB

            session = get_db_session()
            import datetime

            today = datetime.date.today()
            # 可选：先删除今天的旧结果
            session.query(StockChoseDB).filter(
                StockChoseDB.date == today, StockChoseDB.rule == "rule4"
            ).delete()
            session.commit()
            # 插入新结果
            for _, row in filter_stock_info.iterrows():
                obj = StockChoseDB(
                    date=today,
                    symbol=row["symbol"],
                    rule="rule4",
                    description=f"{row.get('name', '')} 当前价:{row.get('price', '')} 涨跌幅:{row.get('change_percent', '')}%",
                )
                session.add(obj)
            session.commit()
            session.close()
            log.info("筛选结果已保存到数据库表 stock_chose_data")
            # 输出部分详细股票信息
            for idx, row in filter_stock_info.iterrows():
                log.info(
                    f"股票代码: {row['symbol']}，名称: {row.get('name', '')}，当前价: {row.get('price', '')}，涨跌幅: {row.get('change_percent', '')}%"
                )
    except Exception as e:
        log.info(f"选股规则4执行异常: {e}")


class Rule4(Rule):
    def __init__(self) -> None:
        super().__init__("rule4")

    @staticmethod
    def _is_increasing(series, window_size=5):
        return series.tail(window_size).is_monotonic_increasing
        # 筛选满足条件的日数据（回调30%到40%）

    @staticmethod
    def _is_retraced_by(row, monthly_highs):
        # 获取当前日期对应月份的最高价
        month_high = monthly_highs.loc[row.name.strftime("%Y-%m")]
        # 计算回调幅度
        retrace_ratio = (month_high - row["close"]) / month_high
        return 0.3 <= retrace_ratio <= 0.4

    @staticmethod
    def _chose(row):
        try:
            symbol = row.symbol
            adjust = "hfq"

            session: Session = get_hist_db_session(symbol)
            daily_price_df = pd.read_sql(
                session.query(StockHistoryDB)
                .filter(
                    StockHistoryDB.symbol == symbol,
                    StockHistoryDB.adjust == adjust,
                )
                .statement,
                session.bind,
            )
            if daily_price_df.empty:
                log.info(f"没有找到 {symbol} 的历史数据")
                session.close()
                return False
            daily_price_df["datetime"] = pd.to_datetime(daily_price_df["date"])
            daily_price_df.set_index("datetime", inplace=True)

            end_date = daily_price_df.index.max()
            start_date = end_date - pd.DateOffset(months=3)
            df_last_quarter = daily_price_df.loc[
                (daily_price_df.index >= start_date)
                & (daily_price_df.index <= end_date)
            ]

            # 修正：直接取最近三个月所有日数据中的最大 high
            highest_price = df_last_quarter["high"].max()
            max_row = df_last_quarter[df_last_quarter["high"] == highest_price].iloc[0]
            max_date = max_row.name

            log.info(f"【{symbol}最近三个月最高价统计】")
            log.info(f"  最高价数值: {highest_price:.2f}")
            log.info(
                f"  最高价出现日期: {max_date.strftime('%Y-%m-%d') if hasattr(max_date, 'strftime') else max_date}"
            )
            log.info(
                "  最高价详细信息: "
                f"在{max_date.strftime('%Y-%m-%d') if hasattr(max_date, 'strftime') else max_date}，"
                f"{max_row['symbol']}开盘价为{max_row['open']}元，收盘价为{max_row['close']}元，"
                f"最高价达到{max_row['high']}元，最低价为{max_row['low']}元，成交量{max_row['volume']}手，"
                f"成交额{max_row['amount']}元，涨跌幅{max_row['change_percent']}%，振幅{max_row['amplitude']}%。"
            )

            last_row = daily_price_df.iloc[-1]
            log.info(f"【最后一条股票数据】")
            log.info(f"  收盘价: {last_row['close']:.2f}")
            log.info(
                "  详细信息: "
                f"在{last_row['date']}，{last_row['symbol']}开盘价为{last_row['open']}元，收盘价为{last_row['close']}元，"
                f"最高价为{last_row['high']}元，最低价为{last_row['low']}元，成交量{last_row['volume']}手，"
                f"成交额{last_row['amount']}元，涨跌幅{last_row['change_percent']}%，振幅{last_row['amplitude']}%。"
            )

            retracement_ratio = (highest_price - last_row["close"]) / highest_price
            log.info(f"【回调比例计算】")
            log.info(f"  回调比例: {retracement_ratio:.2%}（收盘价较最高价的回撤幅度）")
            session.close()
            return 0.3 <= retracement_ratio <= 0.4
        except Exception as e:
            log.info(f"异常:{e}")
            return False

    def chose(self):
        # 从数据库读取所有股票信息
        session: Session = get_db_session()
        from core.models._stock import StockSpotDB

        stock_info_df = pd.read_sql(session.query(StockSpotDB).statement, session.bind)
        session.close()

        # 多线程应用选股规则，指定线程数
        THREAD_NUM = 200  # 可根据实际情况调整

        def apply_rule(row):
            return Rule4._chose(row)

        with concurrent.futures.ThreadPoolExecutor(max_workers=THREAD_NUM) as executor:
            results = list(
                executor.map(apply_rule, [row for _, row in stock_info_df.iterrows()])
            )

        stock_info_df["rule4_sinal"] = results
        filter_stock_info = stock_info_df[stock_info_df["rule4_sinal"]]
        return filter_stock_info

    def generate_stock_report(
        self,
        stock_spot_data: pd.DataFrame,
        stock_history_data: pd.DataFrame,
        stock_business_data: pd.DataFrame,
        stock_business_composition: pd.DataFrame,
        stock_pledge_ratio_data: pd.DataFrame,
        report_date: str = None,
    ):
        pass


if __name__ == "__main__":
    stock_chose_rule4()
