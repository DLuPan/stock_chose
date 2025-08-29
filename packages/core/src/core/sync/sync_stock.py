from typing import Dict, List
import akshare as ak
import numpy as np
import datetime
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.database import get_db, get_db_session, init_db, get_hist_db_session
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
    db = get_db_session()
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
    db = get_db_session()
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
                db = get_db_session()
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
    # Convert date strings to datetime objects for comparison
    start_date_dt = datetime.datetime.strptime(start_date, "%Y%m%d").date()
    end_date_dt = datetime.datetime.strptime(end_date, "%Y%m%d").date()

    # Check the latest date in database for this symbol and adjust type
    db = get_hist_db_session(symbol)
    try:
        latest_record = (
            db.query(StockHistoryDB.date)
            .filter(StockHistoryDB.symbol == symbol, StockHistoryDB.adjust == adjust)
            .order_by(StockHistoryDB.date.desc())
            .first()
        )

        if latest_record:
            latest_date = latest_record[0]
            # If latest date is already beyond end_date, skip sync
            if latest_date >= end_date_dt:
                log.info(
                    f"[{symbol}] 最新数据日期 {latest_date} 已超过或等于结束日期 {end_date_dt}，跳过同步"
                )
                return []

            # If latest date is newer than provided start_date, use latest date + 1 day
            if latest_date > start_date_dt:
                new_start_date = latest_date + datetime.timedelta(days=1)
                start_date = new_start_date.strftime("%Y%m%d")
                start_date_dt = new_start_date
                log.info(
                    f"[{symbol}] 使用数据库最新日期后一天作为开始日期: {start_date}"
                )

    finally:
        db.close()

    # If start_date is after end_date, skip sync
    if start_date_dt > end_date_dt:
        log.info(
            f"[{symbol}] 开始日期 {start_date_dt} 已超过结束日期 {end_date_dt}，跳过同步"
        )
        return []

    # Get historical stock data using akshare
    stock_hist_df = ak.stock_zh_a_hist(
        symbol=symbol,
        period=period,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
    )

    # If no data returned, skip database operations
    if stock_hist_df.empty:
        log.info(f"[{symbol}] 未获取到 {start_date} 至 {end_date} 的历史数据")
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

    # Save to database (new file per symbol/adjust)
    db = get_hist_db_session(symbol)
    try:
        # Insert new data (no need to delete since we're doing incremental sync)
        for stock_item in stock_hist:
            db_stock = StockHistoryDB(**stock_item)
            db.merge(db_stock)  # Use merge to handle updates

        db.commit()
        log.info(
            f"[{symbol}] 成功插入 {len(stock_hist)} 条历史记录，调整类型: {adjust}"
        )
    except Exception as e:
        db.rollback()
        log.error(f"[{symbol}] 数据库操作失败: {e}")
        raise
    finally:
        db.close()
    return stock_hist


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
