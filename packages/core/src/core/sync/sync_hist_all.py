import datetime
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.models import (
    StockSpotDB,
    StockSyncTaskDB,
)
from core.database import get_db_session, init_db
from core.logger import log
from .sync_hist import sync_stock_zh_a_hist

# Initialize database on first run
init_db()


def sync_stock_zh_a_hist_all(
    period: str = "daily",
    start_date: str = "19700101",
    end_date: str = "20500101",
    adjust: str = "hfq",
    max_workers: int = 5,
):
    end_date_obj = datetime.datetime.strptime(end_date, "%Y%m%d").date()
    log.info(
        f"开始同步历史数据，结束日期: {end_date_obj}, 复权: {adjust}, 并发: {max_workers}"
    )

    # Step 1: Initialize tasks
    db = get_db_session()
    try:
        # 获取所有symbol和现有任务
        symbols = [s[0] for s in db.query(StockSpotDB.symbol).all() if s[0]]
        existing_symbols = {
            t[0]
            for t in db.query(StockSyncTaskDB.symbol)
            .filter(StockSyncTaskDB.date == end_date_obj)
            .all()
        }

        log.info(f"股票代码: {len(symbols)}, 已有任务: {len(existing_symbols)}")

        # 批量创建新任务
        new_tasks = [
            StockSyncTaskDB(
                date=end_date_obj,
                symbol=symbol,
                status="pending",
                message="等待同步",
                start_time=datetime.datetime.now(),
            )
            for symbol in symbols
            if symbol not in existing_symbols
        ]

        db.bulk_save_objects(new_tasks)
        db.commit()
        log.info(f"新增任务: {len(new_tasks)}")

    except Exception as e:
        db.rollback()
        log.error(f"初始化任务失败: {e}")
        raise
    finally:
        db.close()

    # Step 2: 获取待处理任务
    db = get_db_session()
    try:
        tasks = (
            db.query(StockSyncTaskDB)
            .filter(
                StockSyncTaskDB.date == end_date_obj,
                StockSyncTaskDB.status.in_(["pending", "failed"]),
            )
            .limit(500)
            .all()
        )

        if not tasks:
            log.info("无待处理任务")
            return

        symbols = [task.symbol for task in tasks]
        log.info(f"待处理任务: {len(tasks)}")

    except Exception as e:
        log.error(f"获取任务失败: {e}")
        raise
    finally:
        db.close()

    # Step 3: 并行执行任务
    success = fail = 0
    start_time_total = time.time()

    def process_symbol(symbol):
        start_time = time.time()
        log.info(f"[{symbol}] 开始同步")

        try:
            # 执行同步
            hist = sync_stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
            )

            elapsed = time.time() - start_time
            log.info(f"[{symbol}] 完成，耗时: {elapsed:.2f}s，记录: {len(hist)}")
            time.sleep(random.uniform(1, 3))

            return (symbol, True, None, elapsed, len(hist))

        except Exception as e:
            elapsed = time.time() - start_time
            log.error(f"[{symbol}] 失败，耗时: {elapsed:.2f}s，错误: {str(e)}")
            time.sleep(random.uniform(1, 3))
            return (symbol, False, str(e), elapsed, 0)

    # 更新任务状态
    def update_task_status(symbol, success, message, elapsed, records_count):
        with get_db_session() as db:
            task = (
                db.query(StockSyncTaskDB)
                .filter(
                    StockSyncTaskDB.date == end_date_obj,
                    StockSyncTaskDB.symbol == symbol,
                )
                .first()
            )

            if task:
                task.status = "completed" if success else "failed"
                task.message = message
                task.start_time = (
                    datetime.datetime.now() if success else task.start_time
                )
                task.end_time = datetime.datetime.now()
                task.duration = elapsed
                db.commit()

    # 执行并行任务
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_symbol, symbol): symbol for symbol in symbols
        }

        for idx, future in enumerate(as_completed(futures), 1):
            symbol = futures[future]
            try:
                symbol, ok, err, elapsed, records_count = future.result()
                if ok:
                    success += 1
                else:
                    fail += 1

                # 更新任务状态
                message = f"成功，{records_count}条记录" if ok else f"失败: {err[:100]}"
                update_task_status(symbol, ok, message, elapsed, records_count)

            except Exception as e:
                fail += 1
                log.error(f"[{symbol}] 执行异常: {e}")
                update_task_status(symbol, False, f"执行异常: {e}", 0, 0)

            # 进度日志
            progress = (idx / len(symbols)) * 100
            elapsed_total = time.time() - start_time_total
            avg_time = elapsed_total / idx
            remaining = avg_time * (len(symbols) - idx)

            log.info(
                f"进度 {idx}/{len(symbols)} ({progress:.1f}%) | "
                f"成功:{success} 失败:{fail} | "
                f"耗时:{elapsed_total:.0f}s 剩余:{remaining:.0f}s"
            )

    # 完成统计
    total_elapsed = time.time() - start_time_total
    log.info(
        f"同步完成! 总计: {len(symbols)}, 成功: {success}, 失败: {fail}, "
        f"总耗时: {total_elapsed:.2f}s"
    )