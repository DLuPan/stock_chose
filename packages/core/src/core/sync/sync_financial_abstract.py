import akshare as ak
import pandas as pd
import numpy as np
import traceback
from typing import List, Dict
from core.models import StockFinancialAbstractDB, StockSpotDB
from core.database import get_db_session
from core.logger import log
from .sync_business_composition import format_a_stock_symbol


def sync_stock_financial_abstract(symbol: str) -> List[Dict]:
    """
    同步单个股票的同花顺关键指标数据

    Args:
        symbol: 股票代码，如 "SH688041" 或 "688041"

    Returns:
        List of financial abstract records
    """
    # 格式化股票代码
    formatted_symbol = format_a_stock_symbol(symbol)
    if formatted_symbol != symbol:
        log.info(f"股票代码已从 {symbol} 格式化为 {formatted_symbol}")

    try:
        # 获取同花顺关键指标数据 - 按报告期
        financial_abstract_df = ak.stock_financial_abstract_ths(
            symbol=formatted_symbol.split("SH")[-1].split("SZ")[-1].split("BJ")[-1], 
            indicator="按报告期"
        )
        log.info(f"[{formatted_symbol}] 获取到 {len(financial_abstract_df)} 条关键指标数据")

        if financial_abstract_df.empty:
            log.info(f"[{formatted_symbol}] 未获取到关键指标数据")
            return []

        # 重命名列以匹配数据库模型
        financial_abstract_df.rename(
            columns={
                "报告期": "report_date",
                "净利润": "net_profit",
                "净利润同比增长率": "net_profit_growth_rate",
                "扣非净利润": "non_net_profit",
                "扣非净利润同比增长率": "non_net_profit_growth_rate",
                "营业总收入": "operating_total_income",
                "营业总收入同比增长率": "operating_total_income_growth_rate",
                "基本每股收益": "basic_earnings_per_share",
                "每股净资产": "net_assets_per_share",
                "每股资本公积金": "capital_reserve_per_share",
                "每股未分配利润": "undistributed_profit_per_share",
                "每股经营现金流": "operating_cash_flow_per_share",
                "销售净利率": "sale_net_profit_rate",
                "销售毛利率": "sale_gross_profit_rate",
                "净资产收益率": "roe",
                "净资产收益率-摊薄": "roe_diluted",
                "营业周期": "operating_cycle",
                "存货周转率": "inventory_turnover",
                "存货周转天数": "inventory_turnover_days",
                "应收账款周转天数": "accounts_receivable_turnover_days",
                "流动比率": "current_ratio",
                "速动比率": "quick_ratio",
                "保守速动比率": "conservative_quick_ratio",
                "产权比率": "property_ratio",
                "资产负债率": "asset_liability_ratio",
            },
            inplace=True,
        )

        # 添加股票代码列
        financial_abstract_df["symbol"] = formatted_symbol

        # 处理字符串列中的 NaN 值
        string_columns = financial_abstract_df.select_dtypes(include=["object"]).columns
        financial_abstract_df[string_columns] = financial_abstract_df[string_columns].fillna("")

        # 转换为记录列表
        financial_abstracts = financial_abstract_df.to_dict("records")

        # 保存到数据库
        db = get_db_session()
        try:
            # 删除该股票已有的关键指标数据
            db.query(StockFinancialAbstractDB).filter(
                StockFinancialAbstractDB.symbol == formatted_symbol
            ).delete()
            
            # 批量插入新数据
            if financial_abstracts:
                db.bulk_insert_mappings(StockFinancialAbstractDB, financial_abstracts)
                db.commit()
                log.info(f"[{formatted_symbol}] 成功同步 {len(financial_abstracts)} 条关键指标数据")
            
        except Exception as e:
            db.rollback()
            log.error(f"[{formatted_symbol}] 数据库操作失败: {e}")
            raise
        finally:
            db.close()

        return financial_abstracts

    except Exception as e:
        log.error(f"[{formatted_symbol}] 获取关键指标数据失败: {e}")
        log.error(f"[{formatted_symbol}] 详细错误信息:\n{traceback.format_exc()}")
        raise


def sync_all_stock_financial_abstracts(max_workers: int = 5):
    """
    同步所有股票的关键指标数据

    Args:
        max_workers: 最大并发数
    """
    log.info("开始同步所有股票的关键指标数据")

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

    # 逐个同步关键指标数据
    success_count = 0
    fail_count = 0

    for i, symbol in enumerate(symbols, 1):
        try:
            sync_stock_financial_abstract(symbol)
            success_count += 1
            log.info(f"进度: {i}/{len(symbols)} - [{symbol}] 同步成功")
        except Exception as e:
            fail_count += 1
            log.error(f"进度: {i}/{len(symbols)} - [{symbol}] 同步失败: {e}")
            log.error(f"[{symbol}] 详细错误信息:\n{traceback.format_exc()}")

        # 显示进度
        if i % 100 == 0 or i == len(symbols):
            log.info(
                f"关键指标数据同步进度: {i}/{len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
            )

    log.info(
        f"关键指标数据同步完成，总计: {len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
    )