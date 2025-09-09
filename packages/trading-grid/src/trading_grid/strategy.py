from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import math
import statistics

# 订单类：表示一个交易订单
@dataclass
class Order:
    id: str                    # 订单ID
    side: str                  # 订单方向：'buy'买入 或 'sell'卖出
    price: float               # 订单价格
    size: float                # 订单数量
    status: str = "open"       # 订单状态：open(开放)、filled(已成交)、canceled(已取消)
    level_idx: Optional[int] = None  # 网格层级索引

# 成交记录类：表示一个订单的成交信息
@dataclass
class Fill:
    order_id: str              # 订单ID
    price: float               # 成交价格
    size: float                # 成交数量
    fee_quote: float           # 手续费(以报价货币计)

# 批次类：表示一个持仓批次
@dataclass
class Lot:
    level_idx: int             # 网格层级索引
    price: float               # 成交价格
    size: float                # 持仓数量

# 策略状态类：保存策略运行时的各种状态信息
@dataclass
class StrategyState:
    open_orders: Dict[str, Order] = field(default_factory=dict)  # 当前开放的订单字典
    inventory_base: float = 0.0                                 # 持仓基础资产数量
    cash_quote: float = 0.0                                     # 持有报价资产现金
    realized_pnl_quote: float = 0.0                             # 已实现盈亏(以报价货币计)
    lots: List[Lot] = field(default_factory=list)               # 持仓批次列表
    mode: str = "RUNNING"                                       # 运行模式：RUNNING(运行中)、PAUSED(暂停)、EXITING(退出中)
    last_price: float = 0.0                                     # 最新价格

# 网格交易策略类
class GridStrategy:
    def __init__(self, cfg: dict, broker):
        self.cfg = cfg              # 配置参数
        self.broker = broker        # 交易经纪人接口
        self.state = StrategyState(cash_quote=cfg["allocate_quote"])  # 初始化策略状态
        self.levels = self._build_levels()  # 构建网格价格层级
        self.tick_id = 0            # 计数器

    # ---- 初始化设置 ----
    def _build_levels(self) -> List[float]:
        """
        构建网格价格层级
        """
        lo = float(self.cfg["lower_bound"])    # 网格下界
        hi = float(self.cfg["upper_bound"])    # 网格上界
        n = int(self.cfg["grid_count"])        # 网格数量
        if hi <= lo or n <= 0:
            raise ValueError("Invalid bounds or grid_count")
        step = (hi - lo) / n                   # 计算每个网格的间距
        return [lo + i * step for i in range(n + 1)]  # 返回所有网格价格层级

    # ---- 核心循环 ----
    def on_bar(self, o: float, h: float, l: float, c: float):
        """
        处理K线数据回调
        o: 开盘价, h: 最高价, l: 最低价, c: 收盘价
        """
        if self.state.mode != "RUNNING":
            return
        self.tick_id += 1
        self.state.last_price = c

        # 风险控制：跌破下界时止损
        stop_loss_pct = float(self.cfg.get("stop_loss_pct_below", 0) or 0)
        if stop_loss_pct > 0:
            if c < self.cfg["lower_bound"] * (1 - stop_loss_pct):
                self._exit_all(reason="stop_loss_breakdown")
                return

        # 止盈：突破上界时止盈
        if self.cfg.get("take_profit_breakout", False):
            if c > self.cfg["upper_bound"]:
                self._exit_all(reason="take_profit_breakout")
                return

        # 根据价格变化管理网格订单
        self._manage_grid_orders(c)

        # 执行限制条件
        self._enforce_limits()

    def _manage_grid_orders(self, price: float):
        """
        管理网格订单
        """
        # 在价格下方一个层级放置买单，在持有批次的上方一个层级放置卖单
        # 买单逻辑：确保在当前价格及以下位置有买单
        # 卖单逻辑：为每个持仓批次，在下一个更高层级确保有对应卖单
        for i, lvl in enumerate(self.levels):
            # 如果价格小于等于层级价格，考虑放置买单（仅当我们有报价货币现金且此处没有开放的买单时）
            if price <= lvl:
                self._ensure_buy(i, lvl, price)

        # 为每个持仓批次，确保在下一个更高层级有配对的卖单
        for lot in list(self.state.lots):
            tgt_idx = min(lot.level_idx + 1, len(self.levels) - 1)  # 目标层级索引
            tgt = self.levels[tgt_idx]  # 目标价格
            self._ensure_sell(tgt_idx, tgt, lot.size)

    # ---- 订单辅助方法 ----
    def _ensure_buy(self, level_idx: int, level_price: float, price: float):
        """
        确保在指定层级有买单
        """
        # 检查是否已在此层级有开放的买单
        if any(o for o in self.state.open_orders.values()
               if o.level_idx == level_idx and o.side == "buy" and o.status == "open"):
            return
        # 资金分配：每个活跃买单层级平均分配资金（简单演示）
        reserve = float(self.cfg.get("capital_reserve_pct", 0.0) or 0.0)  # 保留资金比例
        quote_budget = self.cfg["allocate_quote"] * (1 - reserve)        # 可用资金
        active_buy_levels = max(1, sum(1 for v in self.levels if price <= v))  # 活跃买单层级数
        per_level_quote = quote_budget / active_buy_levels               # 每层级资金
        size = max(1e-8, per_level_quote / level_price)                  # 计算订单数量
        fee_rate = float(self.cfg.get("fee_rate", 0))                    # 手续费率
        est_fee = level_price * size * fee_rate                          # 预估手续费
        cost = level_price * size + est_fee                              # 总成本
        if self.state.cash_quote < cost:
            return  # 资金不足

        # 向经纪人提交限价买单
        oid = self.broker.place_limit(side="buy", price=level_price, size=size)
        self.state.open_orders[oid] = Order(id=oid, side="buy", price=level_price, size=size, level_idx=level_idx)

    def _ensure_sell(self, level_idx: int, level_price: float, size: float):
        """
        确保在指定层级有卖单
        """
        if size <= 0:
            return
        # 检查是否已在此层级有开放的卖单
        if any(o for o in self.state.open_orders.values()
               if o.level_idx == level_idx and o.side == "sell" and o.status == "open"):
            return
        # 向经纪人提交限价卖单
        oid = self.broker.place_limit(side="sell", price=level_price, size=size)
        self.state.open_orders[oid] = Order(id=oid, side="sell", price=level_price, size=size, level_idx=level_idx)

    def on_fill(self, fill: Fill):
        """
        处理订单成交回调
        """
        order = self.state.open_orders.get(fill.order_id)
        if not order:  # 未知订单
            return
        order.status = "filled"

        if order.side == "buy":
            # 买入成交：减少现金，增加持仓，添加持仓批次
            self.state.cash_quote -= (fill.price * fill.size + fill.fee_quote)
            self.state.inventory_base += fill.size
            self.state.lots.append(Lot(level_idx=order.level_idx, price=fill.price, size=fill.size))
            # 配对卖单将在下次on_bar调用中确保创建
        else:
            # 卖出成交：增加现金，减少持仓，实现盈亏
            self.state.cash_quote += (fill.price * fill.size - fill.fee_quote)
            self.state.inventory_base -= fill.size
            # 基于FIFO原则实现盈亏：与等于或低于卖出层级的持仓批次匹配
            realized = 0.0
            remaining = fill.size
            keep_lots = []
            for lot in self.state.lots:
                if remaining <= 0:
                    keep_lots.append(lot)
                    continue
                use = min(remaining, lot.size)  # 使用的数量
                realized += (fill.price - lot.price) * use  # 计算此批次的盈亏
                if lot.size > use:
                    # 如果批次数量大于使用数量，保留剩余部分
                    keep_lots.append(Lot(level_idx=lot.level_idx, price=lot.price, size=lot.size - use))
                remaining -= use
            self.state.lots = keep_lots
            self.state.realized_pnl_quote += realized

    def _exit_all(self, reason: str):
        """
        退出所有仓位
        """
        # 取消所有开放订单，通过经纪人以市价平仓
        for o in self.state.open_orders.values():
            if o.status == "open":
                self.broker.cancel(o.id)
                o.status = "canceled"
        mid = self.state.last_price or (self.levels[0] + self.levels[-1]) / 2  # 使用最新价格或中间价格
        if self.state.inventory_base > 0:
            fee_rate = float(self.cfg.get("fee_rate", 0))
            gross = mid * self.state.inventory_base  # 总价值
            fee = gross * fee_rate  # 手续费
            self.state.cash_quote += (gross - fee)
            # 根据平均成本实现盈亏
            if self.state.lots:
                avg_cost = sum(l.price * l.size for l in self.state.lots) / sum(l.size for l in self.state.lots)
                self.state.realized_pnl_quote += (mid - avg_cost) * sum(l.size for l in self.state.lots)
            self.state.inventory_base = 0
            self.state.lots.clear()
        self.state.mode = "PAUSED"

    def _enforce_limits(self):
        """
        执行限制条件：控制最大开放订单数
        """
        max_orders = int(self.cfg.get("max_open_orders", 1000))  # 最大开放订单数
        open_count = sum(1 for o in self.state.open_orders.values() if o.status == "open")
        if open_count > max_orders:
            # 取消距离当前价格最远的订单
            price = self.state.last_price
            open_list = [o for o in self.state.open_orders.values() if o.status == "open"]
            open_list.sort(key=lambda o: abs(o.price - price), reverse=True)  # 按距离排序
            for o in open_list[max_orders:]:
                self.broker.cancel(o.id)
                o.status = "canceled"