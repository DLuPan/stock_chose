import akshare as ak
import numpy as np
import datetime
import pandas as pd
import traceback
import re
from typing import List, Dict
from core.models import StockBusinessCompositionDB, StockSpotDB
from core.database import get_db_session
from core.logger import log


def format_a_stock_symbol(symbol: str) -> str:
    """
    格式化A股股票代码，确保带有适当的市场前缀（SH、SZ或BJ）

    Args:
        symbol: 股票代码，可能是纯数字或已带有前缀

    Returns:
        格式化后的股票代码（带有SH、SZ或BJ前缀）
    """
    # 如果已经带有SH、SZ或BJ前缀，则直接返回
    if symbol.startswith(("SH", "SZ", "BJ")):
        return symbol

    # 根据股票代码规则添加前缀
    # 6开头的为上海股票
    if symbol.startswith("6"):
        return "SH" + symbol
    # 0、3开头的为深圳股票
    elif symbol.startswith(("0", "3")):
        return "SZ" + symbol
    # 4、8开头的为北京股票
    elif symbol.startswith(("4", "8")):
        return "BJ" + symbol
    # 其他情况默认加上SH前缀（但记录警告）
    else:
        log.warning(f"无法确定股票代码 {symbol} 的市场类型，默认使用SH前缀")
        return "SH" + symbol


def sync_stock_business_composition(symbol: str) -> List[Dict]:
    """
    同步单个股票的主营构成数据

    Args:
        symbol: 股票代码，如 "SH688041" 或 "688041"

    Returns:
        List of business composition records
    """
    # 格式化股票代码
    formatted_symbol = format_a_stock_symbol(symbol)
    if formatted_symbol != symbol:
        log.info(f"股票代码已从 {symbol} 格式化为 {formatted_symbol}")

    try:
        # 获取主营构成数据
        business_composition_df = ak.stock_zygc_em(symbol=formatted_symbol)
        log.info(
            f"[{formatted_symbol}] 获取到 {len(business_composition_df)} 条主营构成数据"
        )

        if business_composition_df.empty:
            log.info(f"[{formatted_symbol}] 未获取到主营构成数据")
            return []

        # 重命名列以匹配数据库模型
        business_composition_df.rename(
            columns={
                "股票代码": "symbol",
                "报告日期": "report_date",
                "分类类型": "category_type",
                "主营构成": "main_composition",
                "主营收入": "main_income",
                "收入比例": "income_ratio",
                "主营成本": "main_cost",
                "成本比例": "cost_ratio",
                "主营利润": "main_profit",
                "利润比例": "profit_ratio",
                "毛利率": "gross_margin",
            },
            inplace=True,
        )

        # 添加股票代码列（如果原始数据中没有）
        if "symbol" not in business_composition_df.columns:
            business_composition_df["symbol"] = formatted_symbol

        # 处理日期列
        business_composition_df["report_date"] = pd.to_datetime(
            business_composition_df["report_date"]
        )

        # 处理数值列中的 NaN 值
        numeric_columns = business_composition_df.select_dtypes(
            include=[np.number]
        ).columns
        business_composition_df[numeric_columns] = business_composition_df[
            numeric_columns
        ].fillna(0)

        # 处理字符串列中的 NaN 值
        string_columns = business_composition_df.select_dtypes(
            include=["object"]
        ).columns
        business_composition_df[string_columns] = business_composition_df[
            string_columns
        ].fillna("")

        # 转换为记录列表
        business_compositions = business_composition_df.to_dict("records")

        # 转换 numpy 类型为 Python 原生类型
        for record in business_compositions:
            for key, value in record.items():
                if isinstance(value, np.integer):
                    record[key] = int(value)
                elif isinstance(value, np.floating):
                    record[key] = float(value)
                elif isinstance(value, pd.Timestamp):
                    record[key] = value.date()

        # 保存到数据库
        db = get_db_session()
        try:
            # 删除该股票已有的主营构成数据
            db.query(StockBusinessCompositionDB).filter(
                StockBusinessCompositionDB.symbol == symbol
            ).delete()

            # 批量插入新数据
            batch_size = 500
            for i in range(0, len(business_compositions), batch_size):
                batch = business_compositions[i : i + batch_size]
                db.bulk_insert_mappings(StockBusinessCompositionDB, batch)
                db.commit()
                log.info(
                    f"[{formatted_symbol}] 批量插入第 {i//batch_size + 1} 批数据，记录数: {len(batch)}"
                )

            log.info(
                f"[{formatted_symbol}] 成功同步 {len(business_compositions)} 条主营构成数据"
            )

        except Exception as e:
            db.rollback()
            log.error(f"[{formatted_symbol}] 数据库操作失败: {e}")
            log.error(f"[{formatted_symbol}] 详细错误信息:\n{traceback.format_exc()}")
            raise
        finally:
            db.close()

        return business_compositions

    except Exception as e:
        log.error(f"[{formatted_symbol}] 获取主营构成数据失败: {e}")
        log.error(f"[{formatted_symbol}] 详细错误信息:\n{traceback.format_exc()}")
        raise


def sync_all_stock_business_compositions(max_workers: int = 5):
    """
    同步所有股票的主营构成数据

    Args:
        max_workers: 最大并发数
    """
    log.info("开始同步所有股票的主营构成数据")

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

    # 逐个同步主营构成数据
    success_count = 0
    fail_count = 0

    for i, symbol in enumerate(symbols, 1):
        try:
            sync_stock_business_composition(symbol)
            success_count += 1
            log.info(f"进度: {i}/{len(symbols)} - [{symbol}] 同步成功")
        except Exception as e:
            fail_count += 1
            log.error(f"进度: {i}/{len(symbols)} - [{symbol}] 同步失败: {e}")
            log.error(f"[{symbol}] 详细错误信息:\n{traceback.format_exc()}")

        # 显示进度
        if i % 100 == 0 or i == len(symbols):
            log.info(
                f"主营构成数据同步进度: {i}/{len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
            )

    log.info(
        f"主营构成数据同步完成，总计: {len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
    )
