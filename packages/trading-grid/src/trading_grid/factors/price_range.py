import numpy as np
import pandas as pd
from trading_grid.factors.base import BaseFactor
from trading_grid.factors.utils import register_factor
from trading_grid.factors.factor_config import config


@register_factor
class PriceRangeFactor(BaseFactor):
    factor_name = "price_range"
    factor_cn_name = "价格区间"

    def calculate(self, price_series: pd.Series = None, **kwargs) -> dict:
        if price_series is None or len(price_series) < 1:
            return self.output_format(
                value=None,
                threshold=f"{config.price_range.min_price} ~ {config.price_range.max_price}",
                conclusion="无法获取当前价格",
                is_passed=False,
            )

        current_price = price_series.iloc[-1]

        # 使用配置的价格区间
        is_passed = (
            config.price_range.min_price
            <= current_price
            <= config.price_range.max_price
        )
        conclusion = "价格适中" if is_passed else "价格过高或过低"

        return self.output_format(
            value=round(float(current_price), 2),
            threshold=f"{config.price_range.min_price} ~ {config.price_range.max_price}",
            conclusion=conclusion,
            is_passed=bool(is_passed),
        )
