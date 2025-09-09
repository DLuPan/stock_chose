# 全自动策略选股
交易日每天18点自动按指定规则筛选符合条件的A股股票，每天6点会全量同步历史数据，需要数据的可直接使用[stock_data.db](./stock_data.db)文件，详情见下文数据结构
# 更新说明
- 2025-08-29：基础数据位于bak分支更新截至到20250826，git同步有问题，文件越来越大，改成mysql存储，后续定时更新数据到release
- 2025-08-22：新增基于规则4的报告生成功能[报告路径](./stock_report/)
- 2025-08-13：改用sqllite存储数据提高数据的复用性和可以只执行，使用uv作为项目依赖管理工具
- 2024-12-03：取消规则1、规则2新增规则3的全量股票选股
- 2024-12-09：取消规则3的10、20、30趋势选择，不稳定，没有意义



# 新增sync_hisotry.sh脚本，fork项目后可直接定时运行该脚本自动同步数据
```shell
# 初始化目录
mkdir -f /usr/local/apps/sync_stock
# 移动脚本至sync_stock目录
# 配置定时任务
crontab -e
0 17 * * 1-5 /usr/bin/bash /usr/local/apps/sync_stock/sync_history.sh &
# 查看定时任务
crontab -l
```


# 运行规则如下
 - ~~rule1:100-200亿流通市值&15天内持续收盘价在250日均线上下~~
 - ~~rule2:200-500亿流通市值&15天内持续收盘价在250日均线上下~~
 - ~~rule3:15天内持续收盘价在250日均线上下~~
 - rule4:取月柱的最高点，近三个月 && 当日收盘价，比月柱的最高价，回调了30%～40%


# 项目结构
- core:核心，提供数据同步&数据采集&规则定义的所有内容[doc](./packages/core/README.md)
- bot:机器人，这个主要是将结果同步到telegram[doc](./packages/bot/README.md)

# 数据结构

项目使用 SQLite 数据库，主要表结构如下：

## stock_spot_data（股票现价快照）
- sync_data: 数据同步日期
- symbol: 股票代码（主键）
- index: 公司指数或分类（备用字段）
- name: 公司名称
- price: 当前价格
- change_percent: 涨跌幅（%）
- change_amount: 涨跌额
- volume: 成交量（股）
- amount: 成交额（元）
- amplitude: 振幅（%）
- high: 当日最高价
- low: 当日最低价
- open: 开盘价
- pre_close: 前收盘价
- volume_ratio: 量比
- turnover: 换手率（%）
- pe_ratio: 动态市盈率
- pb_ratio: 市净率
- market_cap: 总市值
- circulating_cap: 流通市值
- speed: 涨跌速率
- min5_change: 5分钟涨跌幅
- day60_change: 60日涨跌幅
- ytd_change: 年初至今涨跌幅

## stock_history_data（股票历史行情）
- date: 交易日（主键）
- symbol: 股票代码（主键）
- adjust: 复权类型（主键，qfq/hfq/none）
- open: 开盘价
- close: 收盘价
- high: 最高价
- low: 最低价
- volume: 成交量（手）
- amount: 成交额（元）
- amplitude: 振幅（%）
- change_percent: 涨跌幅（%）
- change_amount: 涨跌额（元）
- turnover: 换手率（%）

## stock_business_data（主营业务信息）
- symbol: 股票代码（主键）
- main_business: 主营业务
- product_type: 产品类型
- product_name: 产品名称
- business_scope: 经营范围

## stock_business_composition（主营业务构成）
- symbol: 股票代码（主键）
- report_date: 报告日期（主键）
- category_type: 分类类型（主键）
- main_composition: 主营构成
- main_income: 主营收入（元）
- income_ratio: 收入比例
- main_cost: 主营成本（元）
- cost_ratio: 成本比例
- main_profit: 主营利润（元）
- profit_ratio: 利润比例
- gross_margin: 毛利率

## stock_pledge_ratio_data（股票质押比例）
- symbol: 股票代码（主键）
- name: 股票简称
- index: 无用字段
- trade_date: 交易日期（主键）
- industry: 所属行业
- pledge_ratio: 质押比例（%）
- pledge_shares: 质押股数（万股）
- pledge_value: 质押市值（万元）
- pledge_count: 质押笔数
- unrestricted_pledge: 无限售股质押数（万股）
- restricted_pledge: 限售股质押数（万股）
- ytd_change: 近一年涨跌幅（%）
- industry_code: 所属行业代码

## stock_news_data（个股新闻）
- id: 自增ID
- symbol: 股票代码
- keyword: 关键词
- title: 新闻标题
- content: 新闻内容
- publish_time: 发布时间
- source: 新闻来源
- link: 新闻链接

## stock_financial_debt_data（资产负债表数据）
- id: 自增ID
- symbol: 股票代码
- report_date: 报告期
- indicator_name: 指标名称
- indicator_value: 指标值

## stock_research_report_data（个股研报数据）
- id: 自增ID
- symbol: 股票代码
- short_name: 股票简称
- report_name: 报告名称
- rating: 东财评级
- institution: 机构
- monthly_report_count: 近一月个股研报数
- earnings_2024: 2024-盈利预测-收益
- pe_2024: 2024-盈利预测-市盈率
- earnings_2025: 2025-盈利预测-收益
- pe_2025: 2025-盈利预测-市盈率
- earnings_2026: 2026-盈利预测-收益
- pe_2026: 2026-盈利预测-市盈率
- industry: 行业
- date: 日期
- pdf_link: 报告PDF链接

## stock_financial_abstract_data（关键指标数据）
- id: 自增ID
- symbol: 股票代码
- report_date: 报告期
- net_profit: 净利润
- net_profit_growth_rate: 净利润同比增长率
- non_net_profit: 扣非净利润
- non_net_profit_growth_rate: 扣非净利润同比增长率
- operating_total_income: 营业总收入
- operating_total_income_growth_rate: 营业总收入同比增长率
- basic_earnings_per_share: 基本每股收益
- net_assets_per_share: 每股净资产
- capital_reserve_per_share: 每股资本公积金
- undistributed_profit_per_share: 每股未分配利润
- operating_cash_flow_per_share: 每股经营现金流
- sale_net_profit_rate: 销售净利率
- sale_gross_profit_rate: 销售毛利率
- roe: 净资产收益率
- roe_diluted: 净资产收益率-摊薄
- operating_cycle: 营业周期
- inventory_turnover: 存货周转率
- inventory_turnover_days: 存货周转天数
- accounts_receivable_turnover_days: 应收账款周转天数
- current_ratio: 流动比率
- quick_ratio: 速动比率
- conservative_quick_ratio: 保守速动比率
- property_ratio: 产权比率
- asset_liability_ratio: 资产负债率

## stock_financial_analysis_data（财务指标数据）
- id: 自增ID
- symbol: 股票代码
- date: 日期
- diluted_earnings_per_share: 摊薄每股收益(元)
- weighted_earnings_per_share: 加权每股收益(元)
- adjusted_earnings_per_share: 每股收益_调整后(元)
- non_recurring_earnings_per_share: 扣除非经常性损益后的每股收益(元)
- net_assets_per_share_before: 每股净资产_调整前(元)
- net_assets_per_share_after: 每股净资产_调整后(元)
- operating_cash_flow_per_share: 每股经营性现金流(元)
- capital_reserve_per_share: 每股资本公积金(元)
- undistributed_profit_per_share: 每股未分配利润(元)
- adjusted_net_assets_per_share: 调整后的每股净资产(元)
- total_asset_profitability: 总资产利润率(%)
- main_business_profitability: 主营业务利润率(%)
- total_asset_net_profit: 总资产净利润率(%)
- cost_expense_profitability: 成本费用利润率(%)
- operating_profitability: 营业利润率(%)
- main_business_cost_ratio: 主营业务成本率(%)
- sale_net_profit_ratio: 销售净利率(%)
- capital_reward_ratio: 股本报酬率(%)
- net_asset_reward_ratio: 净资产报酬率(%)
- asset_reward_ratio: 资产报酬率(%)
- sale_gross_profit_ratio: 销售毛利率(%)
- three_expenses_ratio: 三项费用比重
- non_main_business_ratio: 非主营比重
- main_profit_ratio: 主营利润比重
- dividend_payment_ratio: 股息发放率(%)
- investment_return_ratio: 投资收益率(%)
- main_business_profit: 主营业务利润(元)
- roe: 净资产收益率(%)
- weighted_roe: 加权净资产收益率(%)
- non_recurring_net_profit: 扣除非经常性损益后的净利润(元)
- main_business_income_growth: 主营业务收入增长率(%)
- net_profit_growth: 净利润增长率(%)
- net_asset_growth: 净资产增长率(%)
- total_asset_growth: 总资产增长率(%)
- accounts_receivable_turnover: 应收账款周转率(次)
- accounts_receivable_turnover_days: 应收账款周转天数(天)
- inventory_turnover_days: 存货周转天数(天)
- inventory_turnover_rate: 存货周转率(次)
- fixed_asset_turnover: 固定资产周转率(次)
- total_asset_turnover: 总资产周转率(次)
- total_asset_turnover_days: 总资产周转天数(天)
- current_asset_turnover: 流动资产周转率(次)
- current_asset_turnover_days: 流动资产周转天数(天)
- equity_turnover: 股东权益周转率(次)
- current_ratio: 流动比率
- quick_ratio: 速动比率
- cash_ratio: 现金比率(%)
- interest_coverage: 利息支付倍数
- long_debt_to_working_capital: 长期债务与营运资金比率(%)
- equity_ratio: 股东权益比率(%)
- long_term_debt_ratio: 长期负债比率(%)
- equity_to_fixed_asset_ratio: 股东权益与固定资产比率(%)
- debt_to_equity_ratio: 负债与所有者权益比率(%)
- long_asset_to_long_fund_ratio: 长期资产与长期资金比率(%)
- capitalization_ratio: 资本化比率(%)
- fixed_asset_net_value_ratio: 固定资产净值率(%)
- capital_immobilization_ratio: 资本固定化比率(%)
- property_ratio: 产权比率(%)
- liquidation_value_ratio: 清算价值比率(%)
- fixed_asset_ratio: 固定资产比重(%)
- asset_liability_ratio: 资产负债率(%)
- total_assets: 总资产(元)
- operating_cash_flow_to_sales_ratio: 经营现金净流量对销售收入比率(%)
- asset_cash_flow_return_ratio: 资产的经营现金流量回报率(%)
- operating_cash_flow_to_net_profit_ratio: 经营现金净流量与净利润的比率(%)
- operating_cash_flow_to_debt_ratio: 经营现金净流量对负债比率(%)
- cash_flow_ratio: 现金流量比率(%)
- short_term_stock_investment: 短期股票投资(元)
- short_term_bond_investment: 短期债券投资(元)
- short_term_other_operating_investment: 短期其它经营性投资(元)
- long_term_stock_investment: 长期股票投资(元)
- long_term_bond_investment: 长期债券投资(元)
- long_term_other_operating_investment: 长期其它经营性投资(元)
- accounts_receivable_within_1_year: 1年以内应收帐款(元)
- accounts_receivable_between_1_and_2_year: 1-2年以内应收帐款(元)
- accounts_receivable_between_2_and_3_year: 2-3年以内应收帐款(元)
- accounts_receivable_within_3_year: 3年以内应收帐款(元)
- prepaid_payment_within_1_year: 1年以内预付货款(元)
- prepaid_payment_between_1_and_2_year: 1-2年以内预付货款(元)
- prepaid_payment_between_2_and_3_year: 2-3年以内预付货款(元)
- prepaid_payment_within_3_year: 3年以内预付货款(元)
- other_receivables_within_1_year: 1年以内其它应收款(元)
- other_receivables_between_1_and_2_year: 1-2年以内其它应收款(元)
- other_receivables_between_2_and_3_year: 2-3年以内其它应收款(元)
- other_receivables_within_3_year: 3年以内其它应收款(元)

## stock_gdhs_data（股东户数详情）
- id: 自增ID
- symbol: 股票代码
- end_date: 股东户数统计截止日
- change_range: 区间涨跌幅，单位:%
- current_gdhs: 股东户数-本次
- previous_gdhs: 股东户数-上次
- gdhs_change: 股东户数-增减
- gdhs_change_rate: 股东户数-增减比例，单位:%
- average_hold_value: 户均持股市值
- average_hold_amount: 户均持股数量
- total_market_value: 总市值
- total_equity: 总股本
- equity_change: 股本变动
- equity_change_reason: 股本变动原因
- announcement_date: 股东户数公告日期
- stock_code: 代码
- stock_name: 名称

## stock_main_holder_data（主要股东）
- id: 自增ID
- symbol: 股票代码
- number: 编号
- holder_name: 股东名称
- hold_amount: 持股数量，单位: 股
- hold_ratio: 持股比例，单位: %
- stock_type: 股本性质
- end_date: 截至日期
- announcement_date: 公告日期
- holder_explain: 股东说明
- holder_total_num: 股东总数
- average_hold_num: 平均持股数，备注: 按总股本计算