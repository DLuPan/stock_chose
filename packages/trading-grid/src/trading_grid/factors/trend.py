import numpy as np
import pandas as pd
from trading_grid.factors.base import BaseFactor
from trading_grid.factors.utils import register_factor
from trading_grid.factors.factor_config import config


@register_factor
class TrendFactor(BaseFactor):
    factor_name = "trend"
    factor_cn_name = "趋势"

    def calculate(self, price_series: pd.Series = None, **kwargs) -> dict:
        if price_series is None:
            return self.output_format(
                value=None,
                threshold=f"{config.trend.min_trend} ~ {config.trend.max_trend}",
                conclusion="数据不足，无法计算趋势",
                is_passed=False,
            )

        # 使用配置的回看天数
        lookback_days = min(config.trend.lookback_days, len(price_series))
        price_series = price_series[-lookback_days:]

        # 计算趋势强度（使用线性回归斜率）
        x = np.arange(len(price_series))
        y = price_series.values
        slope = np.polyfit(x, y, 1)[0]

        # 将斜率标准化为年化涨跌幅
        trend = slope * 252 / np.mean(y)

        # 使用配置的趋势阈值
        is_passed = config.trend.min_trend <= trend <= config.trend.max_trend
        conclusion = "处于震荡区间" if is_passed else "趋势过强，不适合网格"

        return self.output_format(
            value=round(float(trend), 4),
            threshold=f"{config.trend.min_trend} ~ {config.trend.max_trend}",
            conclusion=conclusion,
            is_passed=bool(is_passed),
        )
