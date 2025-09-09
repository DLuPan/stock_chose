import akshare as ak
import pandas as pd
import numpy as np
import traceback
from typing import List, Dict
from core.models import StockResearchReportDB, StockSpotDB
from core.database import get_db_session
from core.logger import log
from .sync_business_composition import format_a_stock_symbol


def sync_stock_research_report(symbol: str) -> List[Dict]:
    """
    同步单个股票的个股研报数据

    Args:
        symbol: 股票代码，如 "SH688041" 或 "688041"

    Returns:
        List of research report records
    """
    # 格式化股票代码
    formatted_symbol = format_a_stock_symbol(symbol)
    if formatted_symbol != symbol:
        log.info(f"股票代码已从 {symbol} 格式化为 {formatted_symbol}")

    try:
        # 获取个股研报数据
        research_report_df = ak.stock_research_report_em(
            symbol=formatted_symbol.split("SH")[-1].split("SZ")[-1].split("BJ")[-1]
        )
        log.info(f"[{formatted_symbol}] 获取到 {len(research_report_df)} 条个股研报数据")

        if research_report_df.empty:
            log.info(f"[{formatted_symbol}] 未获取到个股研报数据")
            return []

        # 重命名列以匹配数据库模型
        research_report_df.rename(
            columns={
                "股票代码": "symbol",
                "股票简称": "short_name",
                "报告名称": "report_name",
                "东财评级": "rating",
                "机构": "institution",
                "近一月个股研报数": "monthly_report_count",
                "2024-盈利预测-收益": "earnings_2024",
                "2024-盈利预测-市盈率": "pe_2024",
                "2025-盈利预测-收益": "earnings_2025",
                "2025-盈利预测-市盈率": "pe_2025",
                "2026-盈利预测-收益": "earnings_2026",
                "2026-盈利预测-市盈率": "pe_2026",
                "行业": "industry",
                "日期": "date",
                "报告PDF链接": "pdf_link",
            },
            inplace=True,
        )

        # 添加股票代码列（如果原始数据中没有）
        if "symbol" not in research_report_df.columns:
            research_report_df["symbol"] = formatted_symbol

        # 处理数值列中的 NaN 值
        numeric_columns = research_report_df.select_dtypes(include=[np.number]).columns
        research_report_df[numeric_columns] = research_report_df[numeric_columns].fillna(0)

        # 处理字符串列中的 NaN 值
        string_columns = research_report_df.select_dtypes(include=["object"]).columns
        research_report_df[string_columns] = research_report_df[string_columns].fillna("")

        # 转换为记录列表
        research_reports = research_report_df.to_dict("records")

        # 转换 numpy 类型为 Python 原生类型
        for record in research_reports:
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
            # 删除该股票已有的个股研报数据
            db.query(StockResearchReportDB).filter(
                StockResearchReportDB.symbol == formatted_symbol
            ).delete()
            
            # 批量插入新数据
            if research_reports:
                db.bulk_insert_mappings(StockResearchReportDB, research_reports)
                db.commit()
                log.info(f"[{formatted_symbol}] 成功同步 {len(research_reports)} 条个股研报数据")
            
        except Exception as e:
            db.rollback()
            log.error(f"[{formatted_symbol}] 数据库操作失败: {e}")
            raise
        finally:
            db.close()

        return research_reports

    except Exception as e:
        log.error(f"[{formatted_symbol}] 获取个股研报数据失败: {e}")
        log.error(f"[{formatted_symbol}] 详细错误信息:\n{traceback.format_exc()}")
        raise


def sync_all_stock_research_reports(max_workers: int = 5):
    """
    同步所有股票的个股研报数据

    Args:
        max_workers: 最大并发数
    """
    log.info("开始同步所有股票的个股研报数据")

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

    # 逐个同步个股研报数据
    success_count = 0
    fail_count = 0

    for i, symbol in enumerate(symbols, 1):
        try:
            sync_stock_research_report(symbol)
            success_count += 1
            log.info(f"进度: {i}/{len(symbols)} - [{symbol}] 同步成功")
        except Exception as e:
            fail_count += 1
            log.error(f"进度: {i}/{len(symbols)} - [{symbol}] 同步失败: {e}")
            log.error(f"[{symbol}] 详细错误信息:\n{traceback.format_exc()}")

        # 显示进度
        if i % 100 == 0 or i == len(symbols):
            log.info(
                f"个股研报数据同步进度: {i}/{len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
            )

    log.info(
        f"个股研报数据同步完成，总计: {len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
    )