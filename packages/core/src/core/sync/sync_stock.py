from typing import Dict, List
import akshare as ak
import numpy as np
import datetime
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.database import get_db, init_db, get_hist_db_session
from core.models import (
    StockSpotDB,
    StockHistoryDB,
    StockSyncTaskDB,
)  # Make sure StockSpotDB's __table_args__ includes {'extend_existing': True}
from core.logger import log
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.models import Base

# Initialize database on first run
init_db()


def sync_stock_zh_a_hist_all(
    period: str = "daily",
    start_date: str = "19700101",
    end_date: str = "20500101",
    adjust: str = "hfq",
    max_workers: int = 5,
):
    # Convert end_date to a date object for querying
    end_date_obj = datetime.datetime.strptime(end_date, "%Y%m%d").date()

    # Step 1: Initialize tasks for all symbols
    db = next(get_db())
    try:
        # Fetch all symbols
        symbols = db.query(StockSpotDB.symbol).all()
        symbols = [s[0] for s in symbols if s[0]]

        # Insert tasks for symbols that don't already have a task
        for symbol in symbols:
            existing_task = (
                db.query(StockSyncTaskDB)
                .filter(
                    StockSyncTaskDB.date == end_date_obj,
                    StockSyncTaskDB.symbol == symbol,
                )
                .first()
            )

            if not existing_task:
                new_task = StockSyncTaskDB(
                    date=end_date_obj,
                    symbol=symbol,
                    status="start",
                    message="Initial sync task created",
                    start_time=datetime.datetime.now(),
                )
                db.add(new_task)
        db.commit()
    finally:
        db.close()

    # Step 2: Fetch the first 500 pending or failed tasks
    db = next(get_db())
    try:
        tasks = (
            db.query(StockSyncTaskDB)
            .filter(
                StockSyncTaskDB.date == end_date_obj,
                StockSyncTaskDB.status.in_(["start", "failed"]),
            )
            .limit(500)
            .all()
        )

        if not tasks:
            log.info(f"No pending or failed tasks found for date: {end_date}")
            return

        symbols = [task.symbol for task in tasks if task.symbol]
    finally:
        db.close()

    total_symbols = len(symbols)
    log.info(f"准备同步 {total_symbols} 个股票历史数据，最大并发数: {max_workers}")

    # Execute tasks in parallel
    success = 0
    fail = 0

    def worker(symbol):
        start_time = time.time()
        log.info(f"[{symbol}] 开始同步历史数据")
        try:
            hist = sync_stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
            )
            elapsed = time.time() - start_time
            log.info(f"[{symbol}] 同步完成，耗时: {elapsed:.2f}s")
            time.sleep(random.uniform(1, 5))  # 每个任务休眠1-5s
            return (symbol, True, None, elapsed)
        except Exception as e:
            elapsed = time.time() - start_time
            log.error(f"[{symbol}] 同步失败，耗时: {elapsed:.2f}s，错误: {e}")
            time.sleep(random.uniform(1, 5))  # 每个任务休眠1-5s
            return (symbol, False, str(e), elapsed)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {
            executor.submit(worker, symbol): symbol for symbol in symbols
        }
        for idx, future in enumerate(as_completed(future_to_symbol), 1):
            symbol = future_to_symbol[future]
            try:
                symbol, ok, err, elapsed = future.result()
                if ok:
                    success += 1
                else:
                    fail += 1
                # Update task status immediately after execution
                db = next(get_db())
                try:
                    task = (
                        db.query(StockSyncTaskDB)
                        .filter(
                            StockSyncTaskDB.date == end_date_obj,
                            StockSyncTaskDB.symbol == symbol,
                        )
                        .first()
                    )
                    if task:
                        task.status = "completed" if ok else "failed"
                        task.message = f"Sync {'completed' if ok else 'failed'}"
                        task.end_time = datetime.datetime.now()
                        task.duration = elapsed if ok else None
                        db.commit()
                finally:
                    db.close()
            except Exception as e:
                fail += 1
                log.error(f"[{symbol}] 未知异常: {e}")
            remaining = total_symbols - idx
            log.info(
                f"进度 [{idx}/{total_symbols}] | 成功:{success} 失败:{fail} 剩余:{remaining} | 当前:{symbol}"
            )


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

    # Save to database (new file per symbol/adjust)
    db = get_hist_db_session(symbol)
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
