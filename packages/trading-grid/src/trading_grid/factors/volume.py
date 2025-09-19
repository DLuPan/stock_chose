import numpy as np
import pandas as pd
from trading_grid.factors.base import BaseFactor
from trading_grid.factors.utils import register_factor
from trading_grid.factors.factor_config import config


@register_factor
class VolumeFactor(BaseFactor):
    factor_name = "volume"
    factor_cn_name = "成交量"

    def calculate(self, volume_series: pd.Series = None, **kwargs) -> dict:
        if volume_series is None:
            return self.output_format(
                value=None,
                threshold=f"> {config.volume.min_volume}手",
                conclusion="数据不足，无法计算平均成交量",
                is_passed=False,
            )

        # 使用配置的回看天数
        lookback_days = min(config.volume.lookback_days, len(volume_series))
        volume_series = volume_series[-lookback_days:]

        # 计算平均日成交量（单位：手）
        avg_volume = np.mean(volume_series) / 100

        # 使用配置的最小成交量标准
        is_passed = avg_volume >= config.volume.min_volume
        conclusion = "流动性充足" if is_passed else "流动性不足"

        return self.output_format(
            value=round(float(avg_volume), 2),
            threshold=f"> {config.volume.min_volume}手",
            conclusion=conclusion,
            is_passed=bool(is_passed),
        )
