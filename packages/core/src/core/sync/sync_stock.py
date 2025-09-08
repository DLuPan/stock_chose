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

# 保留文件以保持向后兼容性，但实际功能已拆分到独立文件中
__all__ = [
    "sync_stock_zh_a_spot_em",
    "sync_stock_zh_a_hist",
    "sync_stock_zh_a_hist_all",
]

# 从其他模块导入函数以保持向后兼容性
from .sync_spot import sync_stock_zh_a_spot_em
from .sync_hist import sync_stock_zh_a_hist
from .sync_hist_all import sync_stock_zh_a_hist_all
