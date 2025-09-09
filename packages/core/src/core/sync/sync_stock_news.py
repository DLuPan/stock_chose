import akshare as ak
import numpy as np
import datetime
import pandas as pd
import traceback
from typing import List, Dict
from core.models import StockNewsDB, StockSpotDB
from core.database import get_db_session
from core.logger import log
from .sync_business_composition import format_a_stock_symbol


def sync_stock_news(symbol: str) -> List[Dict]:
    """
    同步单个股票的新闻资讯数据

    Args:
        symbol: 股票代码，如 "603777"

    Returns:
        List of stock news records
    """
    # 格式化股票代码
    formatted_symbol = format_a_stock_symbol(symbol)
    if formatted_symbol != symbol:
        log.info(f"股票代码已从 {symbol} 格式化为 {formatted_symbol}")

    try:
        # 获取个股新闻数据
        stock_news_df = ak.stock_news_em(symbol=formatted_symbol)
        log.info(f"[{formatted_symbol}] 获取到 {len(stock_news_df)} 条新闻数据")

        if stock_news_df.empty:
            log.info(f"[{formatted_symbol}] 未获取到新闻数据")
            return []

        # 重命名列以匹配数据库模型
        stock_news_df.rename(
            columns={
                "关键词": "keyword",
                "新闻标题": "title",
                "新闻内容": "content",
                "发布时间": "publish_time",
                "文章来源": "source",
                "新闻链接": "link",
            },
            inplace=True,
        )

        # 添加股票代码列
        stock_news_df["symbol"] = symbol

        # 处理日期列
        stock_news_df["publish_time"] = pd.to_datetime(stock_news_df["publish_time"])

        # 处理数值列中的 NaN 值
        numeric_columns = stock_news_df.select_dtypes(include=[np.number]).columns
        stock_news_df[numeric_columns] = stock_news_df[numeric_columns].fillna(0)

        # 处理字符串列中的 NaN 值
        string_columns = stock_news_df.select_dtypes(include=["object"]).columns
        stock_news_df[string_columns] = stock_news_df[string_columns].fillna("")

        # 转换为记录列表
        stock_news = stock_news_df.to_dict("records")

        # 转换 numpy 类型为 Python 原生类型
        for record in stock_news:
            for key, value in record.items():
                if isinstance(value, np.integer):
                    record[key] = int(value)
                elif isinstance(value, np.floating):
                    record[key] = float(value)
                elif isinstance(value, pd.Timestamp):
                    record[key] = value

        # 保存到数据库
        db = get_db_session()
        try:
            # 删除该股票已有的新闻数据（可选，根据业务需求决定是否保留历史数据）
            db.query(StockNewsDB).filter(StockNewsDB.symbol == symbol).delete()

            # 插入新数据
            for record in stock_news:
                db_stock_news = StockNewsDB(**record)
                db.add(db_stock_news)

            db.commit()
            log.info(f"[{formatted_symbol}] 成功同步 {len(stock_news)} 条新闻数据")

        except Exception as e:
            db.rollback()
            log.error(f"[{formatted_symbol}] 数据库操作失败: {e}")
            log.error(f"[{formatted_symbol}] 详细错误信息:\n{traceback.format_exc()}")
            raise
        finally:
            db.close()

        return stock_news

    except Exception as e:
        log.error(f"[{formatted_symbol}] 获取新闻数据失败: {e}")
        log.error(f"[{formatted_symbol}] 详细错误信息:\n{traceback.format_exc()}")
        raise


def sync_all_stock_news():
    """
    同步所有股票的新闻数据
    """
    log.info("开始同步所有股票的新闻数据")

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

    # 逐个同步新闻数据
    success_count = 0
    fail_count = 0

    for i, symbol in enumerate(symbols, 1):
        try:
            sync_stock_news(symbol)
            success_count += 1
            log.info(f"进度: {i}/{len(symbols)} - [{symbol}] 同步成功")
        except Exception as e:
            fail_count += 1
            log.error(f"进度: {i}/{len(symbols)} - [{symbol}] 同步失败: {e}")
            log.error(f"[{symbol}] 详细错误信息:\n{traceback.format_exc()}")

        # 显示进度
        if i % 10 == 0 or i == len(symbols):
            log.info(
                f"新闻数据同步进度: {i}/{len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
            )

    log.info(
        f"新闻数据同步完成，总计: {len(symbols)}, 成功: {success_count}, 失败: {fail_count}"
    )
