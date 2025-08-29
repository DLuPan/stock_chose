from pydantic import BaseModel
from typing import Optional
from sqlalchemy import Column, Float, String, Integer, Date, Text

from core.models.base import Base


class StockSpotDB(Base):
    """SQLAlchemy model for stock spot data"""

    __tablename__ = "stock_spot_data"

    sync_data = Column(Date)  # Date of data synchronization
    symbol = Column(String(20), primary_key=True)  # Stock symbol/ticker
    index = Column(String(50))  # no use, but can be used for company index or category
    name = Column(String(100))  # Company name
    price = Column(Float)  # Current price
    change_percent = Column(Float)  # Percentage change
    change_amount = Column(Float)  # Price change amount
    volume = Column(Float)  # Trading volume (shares)
    amount = Column(Float)  # Trading amount (currency)
    amplitude = Column(Float)  # Price amplitude percentage
    high = Column(Float)  # Highest price today
    low = Column(Float)  # Lowest price today
    open = Column(Float)  # Opening price
    pre_close = Column(Float)  # Previous closing price
    volume_ratio = Column(Float)  # Volume ratio compared to average
    turnover = Column(Float)  # Turnover rate
    pe_ratio = Column(Float)  # Price-to-earnings ratio (dynamic)
    pb_ratio = Column(Float)  # Price-to-book ratio
    market_cap = Column(Float)  # Total market capitalization
    circulating_cap = Column(Float)  # Circulating market cap
    speed = Column(Float)  # Price change speed
    min5_change = Column(Float)  # 5-minute price change
    day60_change = Column(Float)  # 60-day price change percentage
    ytd_change = Column(Float)  # Year-to-date price change percentage


class StockHistoryDB(Base):
    """SQLAlchemy model for historical stock data"""

    __tablename__ = "stock_history_data"

    date = Column(Date, primary_key=True)  # 交易日
    symbol = Column(String(20), primary_key=True)  # 股票代码 (不带市场标识)
    adjust = Column(
        String(10), primary_key=True
    )  # 数据复权 qfq: 返回前复权后的数据; hfq: 返回后复权后的数据; none: 返回不复权的数据
    open = Column(Float)  # 开盘价
    close = Column(Float)  # 收盘价
    high = Column(Float)  # 最高价
    low = Column(Float)  # 最低价
    volume = Column(Integer)  # 成交量 (手)
    amount = Column(Float)  # 成交额 (元)
    amplitude = Column(Float)  # 振幅 (%)
    change_percent = Column(Float)  # 涨跌幅 (%)
    change_amount = Column(Float)  # 涨跌额 (元)
    turnover = Column(Float)  # 换手率 (%)


class StockBusinessDB(Base):
    """SQLAlchemy model for stock business information"""

    __tablename__ = "stock_business_data"

    symbol = Column(String(20), primary_key=True)  # 股票代码
    main_business = Column(Text)  # 主营业务
    product_type = Column(String(100))  # 产品类型
    product_name = Column(String(200))  # 产品名称
    business_scope = Column(Text)  # 经营范围


class StockBusinessCompositionDB(Base):
    """SQLAlchemy model for stock business composition data"""

    __tablename__ = "stock_business_composition"

    symbol = Column(String(20), primary_key=True)  # 股票代码
    report_date = Column(Date, primary_key=True)  # 报告日期
    category_type = Column(String(50), primary_key=True)  # 分类类型
    main_composition = Column(Integer)  # 主营构成
    main_income = Column(Float)  # 主营收入 (元)
    income_ratio = Column(Float)  # 收入比例
    main_cost = Column(Float)  # 主营成本 (元)
    cost_ratio = Column(Float)  # 成本比例
    main_profit = Column(Float)  # 主营利润 (元)
    profit_ratio = Column(Float)  # 利润比例
    gross_margin = Column(Float)  # 毛利率


class StockPledgeRatioDB(Base):
    """SQLAlchemy model for stock pledge ratio data"""

    __tablename__ = "stock_pledge_ratio_data"

    symbol = Column(String(20), primary_key=True)  # 股票代码
    name = Column(String(100))  # 股票简称
    index = Column(String(50))  # 无用
    trade_date = Column(Date, primary_key=True)  # 交易日期
    industry = Column(String(100))  # 所属行业
    pledge_ratio = Column(Float)  # 质押比例 (%)
    pledge_shares = Column(Float)  # 质押股数 (万股)
    pledge_value = Column(Float)  # 质押市值 (万元)
    pledge_count = Column(Float)  # 质押笔数
    unrestricted_pledge = Column(Float)  # 无限售股质押数 (万股)
    restricted_pledge = Column(Float)  # 限售股质押数 (万股)
    ytd_change = Column(Float)  # 近一年涨跌幅 (%)
    industry_code = Column(String(20))  # 所属行业代码
