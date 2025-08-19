from pydantic import BaseModel
from typing import Optional
from sqlalchemy import Column, Float, String, Integer, Date

from core.models.base import Base


class StockSyncTaskDB(Base):
    """SQLAlchemy model for stock sync task data"""

    __tablename__ = "stock_sync_task_data"
    date = Column(Date, primary_key=True)  # 同步日期
    symbol = Column(String, primary_key=True)  # 股票代码
    status = Column(String)  # 同步状态 start, in_progress, completed, failed
    message = Column(String, nullable=True)  # 同步消息
    duration = Column(Float, nullable=True)  # 同步耗时（秒）
    start_time = Column(Date, nullable=True)  # 同步开始时间
    end_time = Column(Date, nullable=True) # 同步结束时间
