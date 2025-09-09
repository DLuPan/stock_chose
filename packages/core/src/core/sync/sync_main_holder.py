import akshare as ak
import pandas as pd
import numpy as np
import traceback
from typing import List, Dict
from core.models import StockMainHolderDB, StockSpotDB
from core.database import get_db_session
from core.logger import log
from .sync_business_composition import format_a_stock_symbol


def sync_stock_main_holder(symbol: str) -> List[Dict]:
    """
    同步单个股票的主要股东数据

    Args:
        symbol: 股票代码，如 "SH688041" 或 "688041"

    Returns:
        List of main holder records
    """
    # 格式化股票代码
    formatted_symbol = format_a_stock_symbol(symbol)
    if formatted_symbol != symbol:
        log.info(f"股票代码已从 {symbol} 格式化为 {formatted_symbol}")

    try:
        # 获取主要股东数据
        main_holder_df = ak.stock_main_stock_holder(
            stock=formatted_symbol.split("SH")[-1].split("SZ")[-1].split("BJ")[-1]
        )
        log.info(f"[{formatted_symbol}] 获取到 {len(main_holder_df)} 条主要股东数据")

        if main_holder_df.empty:
            log.info(f"[{formatted_symbol}] 未获取到主要股东数据")
            return []

        # 重命名列以匹配数据库模型
        main_holder_df.rename(
            columns={
                "编号": "number",
                "股东名称": "holder_name",
                "持股数量": "hold_amount",
                "持股比例": "hold_ratio",
                "股本性质": "stock_type",
                "截至日期": "end_date",
                "公告日期": "announcement_date",
                "股东说明": "holder_explain",
                "股东总数": "holder_total_num",
                "平均持股数": "average_hold_num",
            },
            inplace=True,
        )

        # 添加股票代码列
        main_holder_df["symbol"] = formatted_symbol

        # 处理数值列中的 NaN 值
        numeric_columns = main_holder_df.select_dtypes(include=[np.number]).columns
        main_holder_df[numeric_columns] = main_holder_df[numeric_columns].fillna(0)

        # 处理字符串列中的 NaN 值
        string_columns = main_holder_df.select_dtypes(include=["object"]).columns
        main_holder_df[string_columns] = main_holder_df[string_columns].fillna("")

        # 转换为记录列表
        main_holder_records = main_holder_df.to_dict("records")

        # 转换 numpy 类型为 Python 原生类型
        for record in main_holder_records:
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
            # 删除该股票已有的主要股东数据
            db.query(StockMainHolderDB).filter(
                StockMainHolderDB.symbol == formatted_symbol
            ).delete()
            
            # 批量插入新数据
            if main_holder_records:
                db.bulk_insert_mappings(StockMainHolderDB, main_holder_records)
                db.commit()
                log.info(f"[{formatted_symbol}] 成功同步 {len(main_holder_records)} 条主要股东数据")
            
        except Exception as e:
            db.rollback()
            log.error(f"[{formatted_symbol}] 数据库操作失败: {e}")
            raise
        finally:
            db.close()

        return main_holder_records

    except Exception as e:
        log.error(f"[{formatted_symbol}] 获取主要股东数据失败: {e}")
        log.error(f"[{formatted_symbol}] 详细错误信息:\n{traceback.format_exc()}")
        raise


def sync_all_stock_main_holders(max_workers: int = 5):
    """
    同步所有股票的主要股东数据

    Args:
        max_workers: 最大并发数
    """
    log.info("开始同步所有股票的主要股东数据")

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

    # 逐个同步主要股东数据
    success_count = 0
    fail_count = 0

    for i, symbol in enumerate(symbols, 1):
        try:
            sync_stock_main_holder(symbol)
            success_count += 1
            log.info(f"进度: {i}/{len(symbols)} - [{symbol}] 同步成功")
        except Exception as e:
            fail_count += 1
            log.error(f"进度: {i}/{len(symbols)} - [{symbol}] 同步失败: {e}")
            log.error(f"[{symbol}] 详细错误信息:\n{traceback.format_exc()}")

        # 显示进度
        if i % 100 == 0 or i == len(symbols):
            log.info(
                f"主要股东数据同步进度: {i}/{len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
            )

    log.info(
        f"主要股东数据同步完成，总计: {len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
    )