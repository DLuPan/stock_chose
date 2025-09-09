import akshare as ak
import pandas as pd
import numpy as np
import traceback
from typing import List, Dict
from core.models import StockGdhsDB, StockSpotDB
from core.database import get_db_session
from core.logger import log
from .sync_business_composition import format_a_stock_symbol


def sync_stock_gdhs(symbol: str) -> List[Dict]:
    """
    同步单个股票的股东户数详情数据

    Args:
        symbol: 股票代码，如 "SH688041" 或 "688041"

    Returns:
        List of gdhs records
    """
    # 格式化股票代码
    formatted_symbol = format_a_stock_symbol(symbol)
    if formatted_symbol != symbol:
        log.info(f"股票代码已从 {symbol} 格式化为 {formatted_symbol}")

    try:
        # 获取股东户数详情数据
        gdhs_df = ak.stock_zh_a_gdhs_detail_em(
            symbol=formatted_symbol.split("SH")[-1].split("SZ")[-1].split("BJ")[-1]
        )
        log.info(f"[{formatted_symbol}] 获取到 {len(gdhs_df)} 条股东户数详情数据")

        if gdhs_df.empty:
            log.info(f"[{formatted_symbol}] 未获取到股东户数详情数据")
            return []

        # 重命名列以匹配数据库模型
        gdhs_df.rename(
            columns={
                "股东户数统计截止日": "end_date",
                "区间涨跌幅": "change_range",
                "股东户数-本次": "current_gdhs",
                "股东户数-上次": "previous_gdhs",
                "股东户数-增减": "gdhs_change",
                "股东户数-增减比例": "gdhs_change_rate",
                "户均持股市值": "average_hold_value",
                "户均持股数量": "average_hold_amount",
                "总市值": "total_market_value",
                "总股本": "total_equity",
                "股本变动": "equity_change",
                "股本变动原因": "equity_change_reason",
                "股东户数公告日期": "announcement_date",
                "代码": "stock_code",
                "名称": "stock_name",
            },
            inplace=True,
        )

        # 添加股票代码列
        gdhs_df["symbol"] = formatted_symbol

        # 处理数值列中的 NaN 值
        numeric_columns = gdhs_df.select_dtypes(include=[np.number]).columns
        gdhs_df[numeric_columns] = gdhs_df[numeric_columns].fillna(0)

        # 处理字符串列中的 NaN 值
        string_columns = gdhs_df.select_dtypes(include=["object"]).columns
        gdhs_df[string_columns] = gdhs_df[string_columns].fillna("")

        # 转换为记录列表
        gdhs_records = gdhs_df.to_dict("records")

        # 转换 numpy 类型为 Python 原生类型
        for record in gdhs_records:
            for key, value in record.items():
                if isinstance(value, np.integer):
                    record[key] = int(value)
                elif isinstance(value, np.floating):
                    record[key] = float(value)
                elif isinstance(value, pd.Timestamp):
                    record[key] = str(value)

        # 保存到数据库
        db = get_db_session()
        try:
            # 删除该股票已有的股东户数详情数据
            db.query(StockGdhsDB).filter(
                StockGdhsDB.symbol == formatted_symbol
            ).delete()
            
            # 批量插入新数据
            if gdhs_records:
                db.bulk_insert_mappings(StockGdhsDB, gdhs_records)
                db.commit()
                log.info(f"[{formatted_symbol}] 成功同步 {len(gdhs_records)} 条股东户数详情数据")
            
        except Exception as e:
            db.rollback()
            log.error(f"[{formatted_symbol}] 数据库操作失败: {e}")
            raise
        finally:
            db.close()

        return gdhs_records

    except Exception as e:
        log.error(f"[{formatted_symbol}] 获取股东户数详情数据失败: {e}")
        log.error(f"[{formatted_symbol}] 详细错误信息:\n{traceback.format_exc()}")
        raise


def sync_all_stock_gdhs(max_workers: int = 5):
    """
    同步所有股票的股东户数详情数据

    Args:
        max_workers: 最大并发数
    """
    log.info("开始同步所有股票的股东户数详情数据")

    # 获取所有股票代码
    db = get_db_session()
    try:
        symbols = [s[0] for s in db.query(StockSpotDB.symbol).all() if s[0]]
        log.info(f"获取到 {len(symbols)} 个股票代码")
    except Exception as e:
        log.error(f"获取股票代码失败: {e}")
        log.error(f"详细错误信息:\n{traceback.format_exc()}")
        raise
    finally:
        db.close()

    # 逐个同步股东户数详情数据
    success_count = 0
    fail_count = 0

    for i, symbol in enumerate(symbols, 1):
        try:
            sync_stock_gdhs(symbol)
            success_count += 1
            log.info(f"进度: {i}/{len(symbols)} - [{symbol}] 同步成功")
        except Exception as e:
            fail_count += 1
            log.error(f"进度: {i}/{len(symbols)} - [{symbol}] 同步失败: {e}")
            log.error(f"[{symbol}] 详细错误信息:\n{traceback.format_exc()}")

        # 显示进度
        if i % 100 == 0 or i == len(symbols):
            log.info(
                f"股东户数详情数据同步进度: {i}/{len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
            )

    log.info(
        f"股东户数详情数据同步完成，总计: {len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
    )