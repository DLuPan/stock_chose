from pydantic import BaseModel
from typing import Optional
from sqlalchemy import Column, Float, String, Integer, Date

from core.models.base import Base


class StockChoseDB(Base):
    """SQLAlchemy model for stock chose data"""

    __tablename__ = "stock_chose_data"
    date = Column(Date, primary_key=True)  # 选股日期
    symbol = Column(String(20), primary_key=True)  # 股票代码
    rule = Column(String(50), primary_key=True)  # 选股规则
    description = Column(String(200))  # 选股描述
