import numpy as np
import pandas as pd
from trading_grid.factors.base import BaseFactor
from trading_grid.factors.utils import register_factor
from trading_grid.factors.factor_config import config


@register_factor
class VolatilityFactor(BaseFactor):
    factor_name = "volatility"
    factor_cn_name = "波动率"

    def calculate(self, price_series: pd.Series = None, **kwargs) -> dict:
        if price_series is None or len(price_series) < 2:
            return self.output_format(
                value=None,
                threshold=f"{config.volatility.min_volatility} - {config.volatility.max_volatility}",
                conclusion="数据不足，无法计算波动率",
                is_passed=False,
            )

        # 使用配置的回看天数
        lookback_days = min(config.volatility.lookback_days, len(price_series))
        price_series = price_series[-lookback_days:]

        returns = price_series.pct_change().dropna()
        volatility = np.std(returns) * np.sqrt(252)

        is_passed = (
            config.volatility.min_volatility
            <= volatility
            <= config.volatility.max_volatility
        )
        conclusion = "适中，适合网格" if is_passed else "波动率过低或过高，不适合网格"

        return self.output_format(
            value=round(float(volatility), 4),
            threshold=f"{config.volatility.min_volatility} - {config.volatility.max_volatility}",
            conclusion=conclusion,
            is_passed=bool(is_passed),
        )
