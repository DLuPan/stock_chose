from typing import Dict, List
import akshare as ak
import numpy as np
import datetime
from core.models import StockHistoryDB
from core.database import get_db_session, get_hist_db_session
from core.logger import log


def format_stock_symbol(symbol: str) -> str:
    """
    Remove exchange prefix from stock symbol if present
    
    Args:
        symbol: Stock symbol with or without exchange prefix (e.g., SH600004 or 600004)
        
    Returns:
        Stock symbol without exchange prefix (e.g., 600004)
    """
    if symbol.startswith(("SH", "SZ", "BJ")):
        return symbol[2:]
    return symbol


def sync_stock_zh_a_hist(
    symbol: str = "000001",
    period: str = "daily",
    start_date: str = "19700101",
    end_date: str = "20500101",
    adjust: str = "none",
) -> List[Dict]:
    # Remove exchange prefix from symbol for akshare API
    formatted_symbol = format_stock_symbol(symbol)
    
    # Convert date strings to datetime objects for comparison
    start_date_dt = datetime.datetime.strptime(start_date, "%Y%m%d").date()
    end_date_dt = datetime.datetime.strptime(end_date, "%Y%m%d").date()

    # Check the latest date in database for this symbol and adjust type
    db = get_hist_db_session(formatted_symbol)
    try:
        latest_record = (
            db.query(StockHistoryDB.date)
            .filter(StockHistoryDB.symbol == formatted_symbol, StockHistoryDB.adjust == adjust)
            .order_by(StockHistoryDB.date.desc())
            .first()
        )

        if latest_record:
            latest_date = latest_record[0]
            # If latest date is already beyond end_date, skip sync
            if latest_date >= end_date_dt:
                log.info(
                    f"[{formatted_symbol}] 最新数据日期 {latest_date} 已超过或等于结束日期 {end_date_dt}，跳过同步"
                )
                return []

            # If latest date is newer than provided start_date, use latest date + 1 day
            if latest_date > start_date_dt:
                new_start_date = latest_date + datetime.timedelta(days=1)
                start_date = new_start_date.strftime("%Y%m%d")
                start_date_dt = new_start_date
                log.info(
                    f"[{formatted_symbol}] 使用数据库最新日期后一天作为开始日期: {start_date}"
                )

    finally:
        db.close()

    # If start_date is after end_date, skip sync
    if start_date_dt > end_date_dt:
        log.info(
            f"[{formatted_symbol}] 开始日期 {start_date_dt} 已超过结束日期 {end_date_dt}，跳过同步"
        )
        return []

    # Get historical stock data using akshare
    stock_hist_df = ak.stock_zh_a_hist(
        symbol=formatted_symbol,
        period=period,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
    )

    # If no data returned, skip database operations
    if stock_hist_df.empty:
        log.info(f"[{formatted_symbol}] 未获取到 {start_date} 至 {end_date} 的历史数据")
        return []

    # Rename columns to English
    stock_hist_df.columns = [
        "date",
        "symbol",
        "open",
        "close",
        "high",
        "low",
        "volume",
        "amount",
        "amplitude",
        "change_percent",
        "change_amount",
        "turnover",
    ]

    # Replace NaN values with 0 for numeric columns
    numeric_columns = stock_hist_df.select_dtypes(include=[np.number]).columns
    stock_hist_df[numeric_columns] = stock_hist_df[numeric_columns].fillna(0)

    # Replace NaN values with empty string for string columns
    string_columns = stock_hist_df.select_dtypes(include=["object"]).columns
    stock_hist_df[string_columns] = stock_hist_df[string_columns].fillna("")
    stock_hist_df["adjust"] = adjust  # Add adjust column

    stock_hist = stock_hist_df.to_dict("records")

    # Convert numpy types to Python native types
    for stock_item in stock_hist:
        for key, value in stock_item.items():
            if isinstance(value, np.integer):
                stock_item[key] = int(value)
            elif isinstance(value, np.floating):
                stock_item[key] = float(value)
            elif isinstance(value, np.bool_):
                stock_item[key] = bool(value)

    # Save to database
    db = get_hist_db_session(formatted_symbol)
    try:
        # Batch insert data
        batch_size = 500
        for i in range(0, len(stock_hist), batch_size):
            batch = stock_hist[i : i + batch_size]
            db.bulk_insert_mappings(StockHistoryDB, batch)
            db.commit()
            log.info(
                f"[{formatted_symbol}] 批量插入第 {i//batch_size + 1} 批数据，记录数: {len(batch)}"
            )

        log.info(f"[{formatted_symbol}] 成功同步 {len(stock_hist)} 条历史数据")
        return stock_hist

    except Exception as e:
        db.rollback()
        log.error(f"[{formatted_symbol}] 数据库操作失败: {e}")
        raise

    finally:
        db.close()