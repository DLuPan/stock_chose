#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整增强版：
- 从 stock_data.db + 每个 stock_hist_{symbol}.db 读取数据
- 计算所有股票的回撤率
- 输出 HTML 报告（交互式图表 + K线 + sparkline + DataTables）
- 同时导出 CSV 和 Excel
"""

from __future__ import annotations
import os
import sys
import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime
from core.path import get_project_root
import pandas as pd
from core.logger import log

# ----------------------------- 配置 -----------------------------
DB_DIR = Path(get_project_root()) / "data"
HIST_DIR = DB_DIR / "hist_db"
OUTPUT_DIR = Path(get_project_root()) / "reports"

# ----------------------------- 数据读取 -----------------------------


def read_spot_db(db_path: Path) -> pd.DataFrame:
    """读取实时股票数据"""
    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql("SELECT * FROM stock_spot_data", conn)
        log.info(f"成功读取实时数据，共 {len(df)} 条记录")
        return df
    except Exception as e:
        log.error(f"读取实时数据失败: {e}")
        raise


def read_hist_db(symbol: str, adjust: str = "qfq") -> pd.DataFrame:
    """读取历史数据"""
    db_file = HIST_DIR / f"stock_hist_{symbol}.db"
    if not db_file.exists():
        raise FileNotFoundError(f"历史数据库不存在: {symbol}")

    try:
        with sqlite3.connect(db_file) as conn:
            if adjust == "any":
                df = pd.read_sql(
                    "SELECT date, open, high, low, close FROM stock_history_data", conn
                )
            else:
                df = pd.read_sql(
                    "SELECT date, open, high, low, close FROM stock_history_data WHERE adjust=?",
                    conn,
                    params=(adjust,),
                )
        df["date"] = pd.to_datetime(df["date"])
        log.debug(f"成功读取股票 {symbol} 的历史数据，共 {len(df)} 条记录")
        return df.sort_values("date")
    except Exception as e:
        log.error(f"读取股票 {symbol} 的历史数据失败: {e}")
        raise


def calc_recent_3m_monthly_high(hist_df: pd.DataFrame) -> Tuple[float, List[str]]:
    """计算最近3个月的月最高价"""
    try:
        tmp = hist_df.copy()
        tmp["month"] = tmp["date"].dt.to_period("M")
        monthly = tmp.groupby("month")["high"].max().sort_index()
        last3 = monthly.tail(3)
        monthly_high = float(last3.max())
        months_list = [str(month) for month in last3.index]
        log.debug(f"计算得到最近3个月最高价: {monthly_high}, 月份: {months_list}")
        return monthly_high, months_list
    except Exception as e:
        log.error(f"计算月最高价失败: {e}")
        raise


def calculate_retracement(monthly_high: float, current_price: float) -> float:
    """计算回撤率"""
    if monthly_high <= 0:
        log.warning(f"月最高价无效: {monthly_high}")
        return 0.0
    return (monthly_high - current_price) / monthly_high


# ----------------------------- 数据处理 -----------------------------


def process_stock_data(
    spot_df: pd.DataFrame, adjust: str
) -> Tuple[List[Dict], List[Dict], Dict]:
    """处理股票数据并计算所有股票的回撤率"""
    all_stocks = []
    failures = []
    stats = {"total": len(spot_df), "success": 0, "fail": 0}

    log.info(f"开始处理 {stats['total']} 只股票数据...")

    for idx, (_, stock) in enumerate(spot_df.iterrows(), 1):
        symbol = stock["symbol"]
        name = stock["name"]

        # 每处理100只股票记录一次进度
        if idx % 100 == 0:
            log.info(f"处理进度: {idx}/{stats['total']}")

        log.debug(f"正在处理第 {idx} 只股票: {symbol}({name})")

        try:
            hist_df = read_hist_db(symbol, adjust)
            if hist_df.empty:
                raise ValueError("历史数据为空")

            # 使用历史数据中的最新收盘价作为当前价格
            current_price = float(hist_df.iloc[-1]["close"])
            monthly_high, months = calc_recent_3m_monthly_high(hist_df)

            if current_price <= 0:
                raise ValueError(f"股票价格无效: {current_price}")

            retr = calculate_retracement(monthly_high, current_price)
            retr_percent = retr * 100

            log.debug(
                f"股票 {symbol}({name}) 月最高价: {monthly_high:.2f}, 当前价: {current_price:.2f}, 回撤率: {retr_percent:.2f}%"
            )

            stats["success"] += 1
            stock_record = create_stock_record(
                stock, hist_df, monthly_high, retr, current_price
            )
            all_stocks.append(stock_record)
            log.info(f"✓ 成功处理股票: {symbol}({name}), 回撤率: {retr_percent:.2f}%")

        except Exception as e:
            stats["fail"] += 1
            error_msg = f"处理股票 {symbol}({name}) 时发生错误: {str(e)}"
            failures.append(
                {
                    "symbol": symbol,
                    "name": name,
                    "reason": error_msg,
                }
            )
            log.error(error_msg, exc_info=True)  # 记录完整的异常堆栈
            continue  # 继续处理下一只股票

    return all_stocks, failures, stats


def create_stock_record(
    stock: pd.Series,
    hist_df: pd.DataFrame,
    monthly_high: float,
    retr: float,
    current_price: float,
) -> Dict:
    """创建股票记录"""
    # 确定股票交易所前缀
    symbol = stock["symbol"]
    if symbol.startswith("6"):
        exchange_prefix = "sh"
    elif symbol.startswith(("0", "3")):
        exchange_prefix = "sz"
    else:
        exchange_prefix = "sh"  # 默认

    eastmoney_url = f"https://quote.eastmoney.com/concept/{exchange_prefix}{symbol}.html?from=classic"

    return {
        "symbol": symbol,
        "name": stock["name"],
        "index": stock["index"],
        "industry": stock.get("industry", "未知"),
        "price": current_price,  # 使用历史数据中的最新收盘价
        "monthly_high": monthly_high,
        "retracement": retr,
        "pe_ratio": stock.get("pe_ratio"),
        "pb_ratio": stock.get("pb_ratio"),
        "market_cap": stock.get("market_cap"),
        "eastmoney_url": eastmoney_url,  # 添加东方财富链接
    }


# ----------------------------- 输出处理 -----------------------------


def export_reports(all_stocks: List[Dict], output_dir: Path):
    """导出各种格式的报告"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # CSV导出
    csv_path = output_dir / "stock_report.csv"
    df_export = pd.DataFrame(all_stocks)
    df_export.to_csv(csv_path, index=False, encoding="utf-8-sig")
    log.info(f"CSV报告已导出: {csv_path}")

    # Excel导出
    excel_path = output_dir / "stock_report.xlsx"
    df_export.to_excel(excel_path, index=False)
    log.info(f"Excel报告已导出: {excel_path}")

    return csv_path, excel_path


def generate_html_report(
    all_stocks: List[Dict], failures: List[Dict], output_path: Path
):
    """生成HTML报告"""
    template_path = Path(__file__).parent / "report_template.html"

    try:
        html_template = template_path.read_text(encoding="utf-8")

        # 替换两个JSON数据占位符
        html_content = html_template.replace(
            "/*REPLACE_JSON_DATA*/",
            json.dumps(all_stocks, ensure_ascii=False, default=str),
        ).replace(
            "/*REPLACE_FAILURES_DATA*/",
            json.dumps(failures, ensure_ascii=False, default=str),
        )

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")
        log.info(f"HTML报告已生成: {output_path}")
        return output_path

    except Exception as e:
        log.error(f"生成HTML报告失败: {e}", exc_info=True)
        raise


# ----------------------------- 主函数 -----------------------------


def generate_report(
    adjust: str = "qfq",
    output_dir: str = None,
):
    """生成股票回撤报告"""
    # 确保output_dir是Path对象
    if output_dir is None:
        output_dir = OUTPUT_DIR
    else:
        output_dir = Path(output_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_output = output_dir / f"stock_report_{timestamp}.html"

    log.info("开始生成股票回撤报告...")
    log.info(f"参数: adjust={adjust}")

    try:
        # 读取数据
        spot_db_path = DB_DIR / "stock_data.db"
        log.info(f"从数据库读取实时数据: {spot_db_path}")
        spot_df = read_spot_db(spot_db_path)

        # 处理数据
        all_stocks, failures, stats = process_stock_data(spot_df, adjust)

        # 输出统计信息
        success_rate = (
            (stats["success"] / stats["total"] * 100) if stats["total"] else 0
        )
        log.info(
            f"处理完成: 总数={stats['total']}, "
            f"成功处理={stats['success']}, "
            f"失败={stats['fail']}, "
            f"成功率={success_rate:.2f}%"
        )

        if failures:
            log.warning(f"有 {len(failures)} 个股票处理失败")
            for failure in failures[:5]:  # 只显示前5个失败案例
                log.warning(
                    f"失败案例: {failure['symbol']}({failure.get('name', 'N/A')}) - {failure['reason']}"
                )
            if len(failures) > 5:
                log.warning(f"... 还有 {len(failures) - 5} 个失败案例未显示")

        # 生成报告
        csv_path, excel_path = export_reports(all_stocks, output_dir)
        html_path = generate_html_report(all_stocks, failures, html_output)

        log.info(f"报告生成完成:")
        log.info(f"  - CSV: {csv_path}")
        log.info(f"  - Excel: {excel_path}")
        log.info(f"  - HTML: {html_path}")

        return {
            "all_stocks": all_stocks,
            "failures": failures,
            "stats": stats,
            "output_files": {"csv": csv_path, "excel": excel_path, "html": html_path},
        }

    except Exception as e:
        log.error(f"生成报告失败: {e}", exc_info=True)
        raise
