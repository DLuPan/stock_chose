# 全自动策略选股
交易日每天18点自动按指定规则筛选符合条件的A股股票，每天6点会全量同步历史数据，需要数据的可直接使用[stock_data.db](./stock_data.db)文件，详情见下文数据结构
# 更新说明
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