from pydantic import BaseModel
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Date, Text, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base

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

    id = Column(Integer, primary_key=True, autoincrement=True)  # 自增ID
    symbol = Column(String(20))  # 股票代码
    report_date = Column(Date)  # 报告日期
    category_type = Column(String(50))  # 分类类型
    main_composition = Column(String(500))  # 主营构成
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


class StockNewsDB(Base):
    """SQLAlchemy model for stock news data"""

    __tablename__ = "stock_news_data"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 自增ID
    symbol = Column(String(20), nullable=False)  # 股票代码
    keyword = Column(String(100))  # 关键词
    title = Column(String(200), nullable=False)  # 新闻标题
    content = Column(Text)  # 新闻内容
    publish_time = Column(DateTime, nullable=False)  # 发布时间
    source = Column(String(100))  # 新闻来源
    link = Column(String(300))  # 新闻链接


class StockFinancialDebtDB(Base):
    """SQLAlchemy model for stock financial debt data (balance sheet from THS)"""

    __tablename__ = "stock_financial_debt_data"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 自增ID
    symbol = Column(String(20), nullable=False)  # 股票代码
    report_date = Column(String(20), nullable=False)  # 报告期
    indicator_name = Column(String(100), nullable=False)  # 指标名称
    indicator_value = Column(String(50))  # 指标值


class StockResearchReportDB(Base):
    """SQLAlchemy model for stock research report data"""

    __tablename__ = "stock_research_report_data"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 自增ID
    symbol = Column(String(20), nullable=False)  # 股票代码
    short_name = Column(String(50))  # 股票简称
    report_name = Column(String(200))  # 报告名称
    rating = Column(String(20))  # 东财评级
    institution = Column(String(100))  # 机构
    monthly_report_count = Column(Integer)  # 近一月个股研报数
    earnings_2024 = Column(Float)  # 2024-盈利预测-收益
    pe_2024 = Column(Float)  # 2024-盈利预测-市盈率
    earnings_2025 = Column(Float)  # 2025-盈利预测-收益
    pe_2025 = Column(Float)  # 2025-盈利预测-市盈率
    earnings_2026 = Column(Float)  # 2026-盈利预测-收益
    pe_2026 = Column(Float)  # 2026-盈利预测-市盈率
    industry = Column(String(50))  # 行业
    date = Column(String(20))  # 日期
    pdf_link = Column(String(300))  # 报告PDF链接


class StockFinancialAbstractDB(Base):
    """SQLAlchemy model for stock financial abstract data (key financial indicators from THS)"""

    __tablename__ = "stock_financial_abstract_data"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 自增ID
    symbol = Column(String(20), nullable=False)  # 股票代码
    report_date = Column(String(20))  # 报告期
    net_profit = Column(String(50))  # 净利润
    net_profit_growth_rate = Column(String(50))  # 净利润同比增长率
    non_net_profit = Column(String(50))  # 扣非净利润
    non_net_profit_growth_rate = Column(String(50))  # 扣非净利润同比增长率
    operating_total_income = Column(String(50))  # 营业总收入
    operating_total_income_growth_rate = Column(String(50))  # 营业总收入同比增长率
    basic_earnings_per_share = Column(String(50))  # 基本每股收益
    net_assets_per_share = Column(String(50))  # 每股净资产
    capital_reserve_per_share = Column(String(50))  # 每股资本公积金
    undistributed_profit_per_share = Column(String(50))  # 每股未分配利润
    operating_cash_flow_per_share = Column(String(50))  # 每股经营现金流
    sale_net_profit_rate = Column(String(50))  # 销售净利率
    sale_gross_profit_rate = Column(String(50))  # 销售毛利率
    roe = Column(String(50))  # 净资产收益率
    roe_diluted = Column(String(50))  # 净资产收益率-摊薄
    operating_cycle = Column(String(50))  # 营业周期
    inventory_turnover = Column(String(50))  # 存货周转率
    inventory_turnover_days = Column(String(50))  # 存货周转天数
    accounts_receivable_turnover_days = Column(String(50))  # 应收账款周转天数
    current_ratio = Column(String(50))  # 流动比率
    quick_ratio = Column(String(50))  # 速动比率
    conservative_quick_ratio = Column(String(50))  # 保守速动比率
    property_ratio = Column(String(50))  # 产权比率
    asset_liability_ratio = Column(String(50))  # 资产负债率


class StockFinancialAnalysisDB(Base):
    """SQLAlchemy model for stock financial analysis data (financial indicators from Sina)"""

    __tablename__ = "stock_financial_analysis_data"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 自增ID
    symbol = Column(String(20), nullable=False)  # 股票代码
    date = Column(String(20))  # 日期
    diluted_earnings_per_share = Column(Float)  # 摊薄每股收益(元)
    weighted_earnings_per_share = Column(Float)  # 加权每股收益(元)
    adjusted_earnings_per_share = Column(Float)  # 每股收益_调整后(元)
    non_recurring_earnings_per_share = Column(Float)  # 扣除非经常性损益后的每股收益(元)
    net_assets_per_share_before = Column(Float)  # 每股净资产_调整前(元)
    net_assets_per_share_after = Column(Float)  # 每股净资产_调整后(元)
    operating_cash_flow_per_share = Column(Float)  # 每股经营性现金流(元)
    capital_reserve_per_share = Column(Float)  # 每股资本公积金(元)
    undistributed_profit_per_share = Column(Float)  # 每股未分配利润(元)
    adjusted_net_assets_per_share = Column(Float)  # 调整后的每股净资产(元)
    total_asset_profitability = Column(Float)  # 总资产利润率(%)
    main_business_profitability = Column(Float)  # 主营业务利润率(%)
    total_asset_net_profit = Column(Float)  # 总资产净利润率(%)
    cost_expense_profitability = Column(Float)  # 成本费用利润率(%)
    operating_profitability = Column(Float)  # 营业利润率(%)
    main_business_cost_ratio = Column(Float)  # 主营业务成本率(%)
    sale_net_profit_ratio = Column(Float)  # 销售净利率(%)
    capital_reward_ratio = Column(Float)  # 股本报酬率(%)
    net_asset_reward_ratio = Column(Float)  # 净资产报酬率(%)
    asset_reward_ratio = Column(Float)  # 资产报酬率(%)
    sale_gross_profit_ratio = Column(Float)  # 销售毛利率(%)
    three_expenses_ratio = Column(Float)  # 三项费用比重
    non_main_business_ratio = Column(Float)  # 非主营比重
    main_profit_ratio = Column(Float)  # 主营利润比重
    dividend_payment_ratio = Column(Float)  # 股息发放率(%)
    investment_return_ratio = Column(Float)  # 投资收益率(%)
    main_business_profit = Column(Float)  # 主营业务利润(元)
    roe = Column(Float)  # 净资产收益率(%)
    weighted_roe = Column(Float)  # 加权净资产收益率(%)
    non_recurring_net_profit = Column(Float)  # 扣除非经常性损益后的净利润(元)
    main_business_income_growth = Column(Float)  # 主营业务收入增长率(%)
    net_profit_growth = Column(Float)  # 净利润增长率(%)
    net_asset_growth = Column(Float)  # 净资产增长率(%)
    total_asset_growth = Column(Float)  # 总资产增长率(%)
    accounts_receivable_turnover = Column(Float)  # 应收账款周转率(次)
    accounts_receivable_turnover_days = Column(Float)  # 应收账款周转天数(天)
    inventory_turnover_days = Column(Float)  # 存货周转天数(天)
    inventory_turnover_rate = Column(Float)  # 存货周转率(次)
    fixed_asset_turnover = Column(Float)  # 固定资产周转率(次)
    total_asset_turnover = Column(Float)  # 总资产周转率(次)
    total_asset_turnover_days = Column(Float)  # 总资产周转天数(天)
    current_asset_turnover = Column(Float)  # 流动资产周转率(次)
    current_asset_turnover_days = Column(Float)  # 流动资产周转天数(天)
    equity_turnover = Column(Float)  # 股东权益周转率(次)
    current_ratio = Column(Float)  # 流动比率
    quick_ratio = Column(Float)  # 速动比率
    cash_ratio = Column(Float)  # 现金比率(%)
    interest_coverage = Column(Float)  # 利息支付倍数
    long_debt_to_working_capital = Column(Float)  # 长期债务与营运资金比率(%)
    equity_ratio = Column(Float)  # 股东权益比率(%)
    long_term_debt_ratio = Column(Float)  # 长期负债比率(%)
    equity_to_fixed_asset_ratio = Column(Float)  # 股东权益与固定资产比率(%)
    debt_to_equity_ratio = Column(Float)  # 负债与所有者权益比率(%)
    long_asset_to_long_fund_ratio = Column(Float)  # 长期资产与长期资金比率(%)
    capitalization_ratio = Column(Float)  # 资本化比率(%)
    fixed_asset_net_value_ratio = Column(Float)  # 固定资产净值率(%)
    capital_immobilization_ratio = Column(Float)  # 资本固定化比率(%)
    property_ratio = Column(Float)  # 产权比率(%)
    liquidation_value_ratio = Column(Float)  # 清算价值比率(%)
    fixed_asset_ratio = Column(Float)  # 固定资产比重(%)
    asset_liability_ratio = Column(Float)  # 资产负债率(%)
    total_assets = Column(Float)  # 总资产(元)
    operating_cash_flow_to_sales_ratio = Column(
        Float
    )  # 经营现金净流量对销售收入比率(%)
    asset_cash_flow_return_ratio = Column(Float)  # 资产的经营现金流量回报率(%)
    operating_cash_flow_to_net_profit_ratio = Column(
        Float
    )  # 经营现金净流量与净利润的比率(%)
    operating_cash_flow_to_debt_ratio = Column(Float)  # 经营现金净流量对负债比率(%)
    cash_flow_ratio = Column(Float)  # 现金流量比率(%)
    short_term_stock_investment = Column(Float)  # 短期股票投资(元)
    short_term_bond_investment = Column(Float)  # 短期债券投资(元)
    short_term_other_operating_investment = Column(Float)  # 短期其它经营性投资(元)
    long_term_stock_investment = Column(Float)  # 长期股票投资(元)
    long_term_bond_investment = Column(Float)  # 长期债券投资(元)
    long_term_other_operating_investment = Column(Float)  # 长期其它经营性投资(元)
    accounts_receivable_within_1_year = Column(Float)  # 1年以内应收帐款(元)
    accounts_receivable_between_1_and_2_year = Column(Float)  # 1-2年以内应收帐款(元)
    accounts_receivable_between_2_and_3_year = Column(Float)  # 2-3年以内应收帐款(元)
    accounts_receivable_within_3_year = Column(Float)  # 3年以内应收帐款(元)
    prepaid_payment_within_1_year = Column(Float)  # 1年以内预付货款(元)
    prepaid_payment_between_1_and_2_year = Column(Float)  # 1-2年以内预付货款(元)
    prepaid_payment_between_2_and_3_year = Column(Float)  # 2-3年以内预付货款(元)
    prepaid_payment_within_3_year = Column(Float)  # 3年以内预付货款(元)
    other_receivables_within_1_year = Column(Float)  # 1年以内其它应收款(元)
    other_receivables_between_1_and_2_year = Column(Float)  # 1-2年以内其它应收款(元)
    other_receivables_between_2_and_3_year = Column(Float)  # 2-3年以内其它应收款(元)
    other_receivables_within_3_year = Column(Float)  # 3年以内其它应收款(元)


class StockGdhsDB(Base):
    """SQLAlchemy model for stock gdhs data (股东户数详情 from EM)"""

    __tablename__ = "stock_gdhs_data"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 自增ID
    symbol = Column(String(20), nullable=False)  # 股票代码
    end_date = Column(String(20))  # 股东户数统计截止日
    change_range = Column(Float)  # 区间涨跌幅，单位:%
    current_gdhs = Column(Integer)  # 股东户数-本次
    previous_gdhs = Column(Integer)  # 股东户数-上次
    gdhs_change = Column(Integer)  # 股东户数-增减
    gdhs_change_rate = Column(Float)  # 股东户数-增减比例，单位:%
    average_hold_value = Column(Float)  # 户均持股市值
    average_hold_amount = Column(Float)  # 户均持股数量
    total_market_value = Column(Float)  # 总市值
    total_equity = Column(BigInteger)  # 总股本
    equity_change = Column(BigInteger)  # 股本变动
    equity_change_reason = Column(String(200))  # 股本变动原因
    announcement_date = Column(String(20))  # 股东户数公告日期
    stock_code = Column(String(20))  # 代码
    stock_name = Column(String(50))  # 名称


class StockMainHolderDB(Base):
    """SQLAlchemy model for stock main holder data (主要股东 from Sina)"""

    __tablename__ = "stock_main_holder_data"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 自增ID
    symbol = Column(String(20), nullable=False)  # 股票代码
    number = Column(String(20))  # 编号
    holder_name = Column(String(100))  # 股东名称
    hold_amount = Column(Float)  # 持股数量，单位: 股
    hold_ratio = Column(Float)  # 持股比例，单位: %
    stock_type = Column(String(50))  # 股本性质
    end_date = Column(String(20))  # 截至日期
    announcement_date = Column(String(20))  # 公告日期
    holder_explain = Column(String(500))  # 股东说明
    holder_total_num = Column(Float)  # 股东总数
    average_hold_num = Column(Float)  # 平均持股数，备注: 按总股本计算
