from typing import Dict, List
import akshare as ak
import numpy as np
import datetime
import time
import random
from core.database import get_db, init_db
from core.models import (
    StockSpotDB,
    StockHistoryDB,
)  # Make sure StockSpotDB's __table_args__ includes {'extend_existing': True}
from core.logger import log

# Initialize database on first run
init_db()


def sync_stock_zh_a_hist_all(
    period: str = "daily",
    start_date: str = "19700101",
    end_date: str = "20500101",
    adjust: str = "hfq",
):
    db = next(get_db())
    try:
        symbols = db.query(StockSpotDB.symbol).all()
        symbols = [s[0] for s in symbols if s[0]]  # 提取 symbol 字符串
    finally:
        db.close()
    total = len(symbols)
    success = 0
    fail = 0
    for idx, symbol in enumerate(symbols, 1):
        log.info(f"Syncing historical data for symbol: {symbol}")
        try:
            hist = sync_stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
            )
            success += 1
        except Exception as e:
            log.error(f"Error syncing {symbol}: {e}")
            fail += 1
        remaining = total - idx
        # 使用loguru的log.info打印进度条
        log.info(
            f"[{idx}/{total}] 成功:{success} 失败:{fail} 剩余:{remaining} | 当前:{symbol}"
        )
        time.sleep(random.uniform(1, 5))  # 每次调用休眠1-5s随机


def sync_stock_zh_a_hist(
    symbol: str = "000001",
    period: str = "daily",
    start_date: str = "19700101",
    end_date: str = "20500101",
    adjust: str = "none",
) -> List[Dict]:
    # Get historical stock data using akshare
    stock_hist_df = ak.stock_zh_a_hist(
        symbol=symbol,
        period=period,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
    )

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

    # Save to database
    db = next(get_db())
    try:
        for stock_item in stock_hist:
            db_stock = StockHistoryDB(**stock_item)
            db.merge(db_stock)  # Use merge to handle updates
        db.commit()
    finally:
        db.close()
    return stock_hist


def sync_stock_zh_a_spot_em():
    """
    Sync stock data.
    """
    # Get real-time stock data using akshare
    stock_df = ak.stock_zh_a_spot_em()

    # Rename columns to English
    stock_df.columns = [
        "index",
        "symbol",
        "name",
        "price",
        "change_percent",
        "change_amount",
        "volume",
        "amount",
        "amplitude",
        "high",
        "low",
        "open",
        "pre_close",
        "volume_ratio",
        "turnover",
        "pe_ratio",
        "pb_ratio",
        "market_cap",
        "circulating_cap",
        "speed",
        "min5_change",
        "day60_change",
        "ytd_change",
    ]

    # Replace NaN values with 0 for numeric columns
    numeric_columns = stock_df.select_dtypes(include=[np.number]).columns
    stock_df[numeric_columns] = stock_df[numeric_columns].fillna(0)

    # Replace NaN values with empty string for string columns
    string_columns = stock_df.select_dtypes(include=["object"]).columns
    stock_df[string_columns] = stock_df[string_columns].fillna("")
    stock_df["sync_data"] = datetime.datetime.now()  # Add adjust column
    stocks = stock_df.to_dict("records")

    # Convert numpy types to Python native types
    for stock in stocks:
        for key, value in stock.items():
            if isinstance(value, np.integer):
                stock[key] = int(value)
            elif isinstance(value, np.floating):
                stock[key] = float(value)

    # Save to database
    db = next(get_db())
    try:
        for stock in stocks:
            db_stock = StockSpotDB(**stock)
            db.merge(db_stock)  # Use merge to handle updates
        db.commit()
    finally:
        db.close()

    return stocks
