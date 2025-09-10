import numpy as np
import pandas as pd
from trading_grid.factors.base import BaseFactor
from trading_grid.factors.utils import register_factor


@register_factor
class VolatilityFactor(BaseFactor):
    factor_name = "volatility"
    factor_cn_name = "波动率"

    def calculate(self, price_series: pd.Series = None, **kwargs) -> dict:
        if price_series is None or len(price_series) < 2:
            return self.output_format(
                value=None,
                threshold="0.05 - 0.50",
                conclusion="数据不足，无法计算波动率",
                is_passed=False,
            )

        returns = price_series.pct_change().dropna()
        volatility = np.std(returns) * np.sqrt(252)

        is_passed = 0.05 <= volatility <= 0.50
        conclusion = "适中，适合网格" if is_passed else "波动率过低或过高，不适合网格"

        return self.output_format(
            value=round(float(volatility), 4),
            threshold="0.05 - 0.50",
            conclusion=conclusion,
            is_passed=bool(is_passed),  # 确保转换为Python原生bool类型
        )