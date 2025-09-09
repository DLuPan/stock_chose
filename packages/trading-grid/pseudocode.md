# 网格交易伪代码

## 参数
- symbol: 交易对
- base_currency, quote_currency: 基础货币和计价货币
- lower_bound, upper_bound: 价格上下限
- grid_count (N): 网格数量
- allocate_quote: 总计价货币资金
- grid_spacing_mode: 网格间距模式：FIXED_% | ATR_K | BBANDS_K
- fee_rate: 手续费率
- take_profit_breakout: bool (是否在突破时止盈)
- stop_loss_pct_below: float (可选，跌破止损百分比)
- trailing_exit_pct: float (可选，追踪止盈百分比)
- capital_reserve_pct: float (例如 0.3，资金保留比例)
- rebalance_on_fill: bool (成交后是否重新平衡)

## 推导值
- grid_levels = linspace(lower_bound, upper_bound, grid_count+1) (网格层级)
- position_sizing per grid = allocate_quote * (1 - reserve) / effective_buy_grids (每网格头寸规模)

## 状态
- open_orders: dict[id -> Order] (未成交订单字典)
- inventory_base: float (持仓基础货币数量)
- cash_quote: float (现金计价货币数量)
- last_price: float (最新价格)
- filled_trades: list[Trade] (已成交交易列表)
- realized_pnl_quote: float (已实现盈亏)
- unrealized_pnl_quote: float (未实现盈亏)
- mode: RUNNING | PAUSED | EXITING (运行模式)

## 事件循环 (每个tick/时间条)
1. 更新指标 (如果启用，更新ATR/布林带)
2. 如果价格突破上界：
   - 如果take_profit_breakout为true：平仓所有头寸，取消不必要的订单
   - 否则：向上移动价格区间或暂停买入订单
3. 如果价格跌破下界：
   - 如果触发stop_loss_pct_below：全部平仓，设置模式为PAUSED
4. 对于每个网格层级g：
   - 如果价格向下穿过g且下方没有未成交的买单：
       在g位置下单买入
   - 如果之前在g位置买入且价格向上穿过g：
       在g位置下单卖出(头寸规模与在g或g以下获得的持仓相匹配)
5. 重新平衡(可选)：转换小额零散持仓/按计划保持中性敞口
6. 风险检查：最大敞口、最大订单数、每日亏损限制
7. 持久化状态(幂等操作)

## 成交处理 (on_fill(order, fill))
- 如果是买入成交：记录该层级的头寸，将匹配的卖出单加入队列(下一个更高层级)
- 如果是卖出成交：实现盈亏，释放资金，可能在下一个更低层级加入买入单(经典网格循环)

## 退出
- 取消所有订单，按市价或退出规则平仓，生成最终报告