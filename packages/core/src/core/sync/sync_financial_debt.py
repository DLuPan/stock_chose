import akshare as ak
import pandas as pd
import numpy as np
import traceback
from typing import List, Dict
from core.models import StockFinancialDebtDB, StockSpotDB
from core.database import get_db_session
from core.logger import log
from .sync_business_composition import format_a_stock_symbol


def sync_stock_financial_debt(symbol: str) -> List[Dict]:
    """
    同步单个股票的同花顺资产负债表数据

    Args:
        symbol: 股票代码，如 "SH688041" 或 "688041"

    Returns:
        List of financial debt records
    """
    # 格式化股票代码
    formatted_symbol = format_a_stock_symbol(symbol)
    if formatted_symbol != symbol:
        log.info(f"股票代码已从 {symbol} 格式化为 {formatted_symbol}")

    try:
        # 获取同花顺资产负债表数据 - 按报告期
        financial_debt_df = ak.stock_financial_debt_ths(
            symbol=formatted_symbol.split("SH")[-1].split("SZ")[-1].split("BJ")[-1],
            indicator="按报告期",
        )
        log.info(
            f"[{formatted_symbol}] 获取到 {len(financial_debt_df)} 条资产负债表数据"
        )

        if financial_debt_df.empty:
            log.info(f"[{formatted_symbol}] 未获取到资产负债表数据")
            return []

        # 添加股票代码列
        financial_debt_df["symbol"] = formatted_symbol

        # 转换为长格式数据
        financial_debt_records = []
        for _, row in financial_debt_df.iterrows():
            report_date = row["报告期"]
            for column in financial_debt_df.columns:
                if column not in ["报告期", "报表核心指标", "报表全部指标", "symbol"]:
                    financial_debt_records.append(
                        {
                            "symbol": formatted_symbol,
                            "report_date": report_date,
                            "indicator_name": column,
                            "indicator_value": row[column],
                        }
                    )

        # 保存到数据库
        db = get_db_session()
        try:
            # 删除该股票已有的资产负债表数据
            db.query(StockFinancialDebtDB).filter(
                StockFinancialDebtDB.symbol == formatted_symbol
            ).delete()

            # 批量插入新数据
            if financial_debt_records:
                db.bulk_insert_mappings(StockFinancialDebtDB, financial_debt_records)
                db.commit()
                log.info(
                    f"[{formatted_symbol}] 成功同步 {len(financial_debt_records)} 条资产负债表数据"
                )

        except Exception as e:
            db.rollback()
            log.error(f"[{formatted_symbol}] 数据库操作失败: {e}")
            raise
        finally:
            db.close()

        return financial_debt_records

    except Exception as e:
        log.error(f"[{formatted_symbol}] 获取资产负债表数据失败: {e}")
        log.error(f"[{formatted_symbol}] 详细错误信息:\n{traceback.format_exc()}")
        raise


def sync_all_stock_financial_debts(max_workers: int = 5):
    """
    同步所有股票的资产负债表数据

    Args:
        max_workers: 最大并发数
    """
    log.info("开始同步所有股票的资产负债表数据")

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

    # 逐个同步资产负债表数据
    success_count = 0
    fail_count = 0

    for i, symbol in enumerate(symbols, 1):
        try:
            sync_stock_financial_debt(symbol)
            success_count += 1
            log.info(f"进度: {i}/{len(symbols)} - [{symbol}] 同步成功")
        except Exception as e:
            fail_count += 1
            log.error(f"进度: {i}/{len(symbols)} - [{symbol}] 同步失败: {e}")
            log.error(f"[{symbol}] 详细错误信息:\n{traceback.format_exc()}")

        # 显示进度
        if i % 100 == 0 or i == len(symbols):
            log.info(
                f"资产负债表数据同步进度: {i}/{len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
            )

    log.info(
        f"资产负债表数据同步完成，总计: {len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
    )
