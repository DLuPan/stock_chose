from trading_grid.factors.base import BaseFactor
from trading_grid.factors.utils import register_factor
from trading_grid.factors.factor_config import config


@register_factor
class MarketCapFactor(BaseFactor):
    factor_name = "market_cap"
    factor_cn_name = "市值"

    def calculate(self, market_cap: float = None, **kwargs) -> dict:
        if market_cap is None:
            return self.output_format(
                value=None,
                threshold=f"{config.market_cap.min_market_cap}亿 ~ {config.market_cap.max_market_cap}亿",
                conclusion="缺少市值数据",
                is_passed=False,
            )

        # 将市值转换为亿元单位
        market_cap_billion = market_cap / 100000000

        # 使用配置的市值区间
        is_passed = (
            config.market_cap.min_market_cap
            <= market_cap_billion
            <= config.market_cap.max_market_cap
        )
        conclusion = "市值适中" if is_passed else "市值过高或过低"

        return self.output_format(
            value=round(float(market_cap_billion), 2),
            threshold=f"{config.market_cap.min_market_cap}亿 ~ {config.market_cap.max_market_cap}亿",
            conclusion=conclusion,
            is_passed=bool(is_passed),
        )
