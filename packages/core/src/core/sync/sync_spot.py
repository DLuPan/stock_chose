from typing import Dict, List
import akshare as ak
import numpy as np
import datetime
from core.models import StockSpotDB
from core.database import get_db_session
from core.logger import log


def sync_stock_zh_a_spot_em():
    """
    Sync stock data with optimized performance. Deletes all existing data before inserting new data.
    """
    try:
        # Get real-time stock data using akshare
        stock_df = ak.stock_zh_a_spot_em()

        log.info(f"Fetched {len(stock_df)} stock records from API")

    except Exception as e:
        log.error(f"Failed to fetch stock data from API: {e}")
        raise

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

    # Add sync timestamp
    stock_df["sync_data"] = datetime.datetime.now()

    # Convert numpy types to Python native types in bulk
    for col in stock_df.select_dtypes(include=[np.integer]).columns:
        stock_df[col] = stock_df[col].astype(int, errors="ignore")
    for col in stock_df.select_dtypes(include=[np.floating]).columns:
        stock_df[col] = stock_df[col].astype(float, errors="ignore")

    # Fill NaN values
    numeric_cols = stock_df.select_dtypes(include=[np.number]).columns
    string_cols = stock_df.select_dtypes(include=["object"]).columns

    stock_df[numeric_cols] = stock_df[numeric_cols].fillna(0)
    stock_df[string_cols] = stock_df[string_cols].fillna("")

    # Convert to records
    stocks = stock_df.to_dict("records")

    # Save to database with batch processing
    db = get_db_session()
    try:
        # Delete all existing data first
        db.query(StockSpotDB).delete()
        log.info("Deleted all existing stock spot data")

        batch_size = 1000
        total_records = len(stocks)

        for i in range(0, total_records, batch_size):
            batch = stocks[i : i + batch_size]
            for stock in batch:
                db_stock = StockSpotDB(**stock)
                db.add(
                    db_stock
                )  # Use add instead of merge since we're doing fresh insert

            db.commit()  # Commit in batches
            log.info(f"Committed batch {i//batch_size + 1}, records: {len(batch)}")

        log.info(f"Successfully synced {total_records} stock records")

    except Exception as e:
        db.rollback()
        log.error(f"Database operation failed: {e}")
        raise
    finally:
        db.close()

    return stocks