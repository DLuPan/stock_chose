from core.rule.base import Rule
import pandas as pd
import numpy as np
import datetime
from copy import deepcopy
import os
import akshare as ak
from core.logger import log


def stock_chose_rule4():
    """
    选股规则4：取月柱的最高点，近三个月 && 当日收盘价，比月柱的最高价，回调了30%～40%
    """
    log.info("开始执行选股规则4")
    rule4 = Rule4()
    filter_stock_info = rule4.chose()
    if filter_stock_info.empty:
        log.info("没有符合规则4的股票")
    else:
        log.info(f"符合规则4的股票数量: {len(filter_stock_info)}")
        filter_stock_info.to_csv(
            f"{os.getcwd()}/data/chose/stock_chose_rule4_{datetime.datetime.now().strftime('%Y_%m_%d')}.csv",
            index=False,
        )


class Rule4(Rule):
    def __init__(self) -> None:
        super().__init__()

    def _SMA(data, window_size):
        """
        使用 Pandas 计算简单移动平均（SMA），并将 NaN 值填充为下一个有效值。

        参数:
            data (pd.Series or pd.DataFrame): 输入的 Pandas 数据对象。
            window_size (int): 移动窗口的大小。

        返回:
            pd.Series: 简单移动平均值序列。
        """
        if isinstance(data, pd.Series):
            sma = data.rolling(window=window_size).mean()
            return sma.fillna(method="bfill")  # 后向填充 NaN 值
        elif isinstance(data, pd.DataFrame):
            sma = data.rolling(window=window_size).mean()
            return sma.fillna(method="bfill")  # 后向填充 NaN 值
        else:
            raise ValueError("输入数据必须是 Pandas DataFrame 或 Series 对象。")

    def _is_increasing(series, window_size=5):
        return series.tail(window_size).is_monotonic_increasing
        # 筛选满足条件的日数据（回调30%到40%）

    def _is_retraced_by(row, monthly_highs):
        # 获取当前日期对应月份的最高价
        month_high = monthly_highs.loc[row.name.strftime("%Y-%m")]
        # 计算回调幅度
        retrace_ratio = (month_high - row["close"]) / month_high
        return 0.3 <= retrace_ratio <= 0.4

    def _chose(row):
        try:
            symobl = row.代码
            adjust = "hfq"

            daily_price = pd.read_csv(
                f"{root_dir}/data/info/stock_{adjust}_{symobl}.csv",
                parse_dates=["datetime"],
            )
            # 确保 datetime 是时间格式
            daily_price["datetime"] = pd.to_datetime(
                daily_price["datetime"]
            )  # 转为 datetime 类型
            daily_price.set_index("datetime", inplace=True)  # 设置为索引
            # 提取10、11、12月的数据
            df_last_quarter = daily_price.loc[
                daily_price.index.month.isin([10, 11, 12])
            ]

            # 计算每月的最高价
            monthly_highs = df_last_quarter.resample("M")["high"].max()
            highest_price = monthly_highs.max()  # 取10、11、12月的总体最高价
            print(f"10、11、12月的最高价: {highest_price}")
            # 获取最后一条数据的收盘价
            last_close_price = daily_price.iloc[-1]["close"]
            print(f"最后一条数据的收盘价: {last_close_price}")
            retracement_ratio = (highest_price - last_close_price) / highest_price
            print(f"回调比例: {retracement_ratio:.2%}")
            return 0.3 <= retracement_ratio <= 0.4
        except Exception as e:
            print(f"异常:{e}")
            return False

    def chose(self):
        # 15天内持续收盘价在250日均线上下&10\20\30线趋势向上
        stock_info = pd.read_csv(f"{root_dir}/data/stock_info.csv", dtype={"代码": str})
        # 250+趋势过滤
        print(stock_info)
        stock_info["rule4_sinal"] = stock_info.apply(Rule4._chose, axis=1)
        filter_stock_info = stock_info[stock_info["rule4_sinal"]]
        filter_stock_info.to_csv(
            f"{root_dir}/data/chose/stock_chose_rule4_{c_date}.csv",
            index=False,
        )
        return filter_stock_info
