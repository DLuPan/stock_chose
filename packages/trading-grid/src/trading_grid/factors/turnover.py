import numpy as np
import pandas as pd
from trading_grid.factors.base import BaseFactor
from trading_grid.factors.utils import register_factor
from trading_grid.factors.factor_config import config


@register_factor
class TurnoverFactor(BaseFactor):
    factor_name = "turnover"
    factor_cn_name = "换手率"

    def calculate(self, turnover_series: pd.Series = None, **kwargs) -> dict:
        if turnover_series is None:
            return self.output_format(
                value=None,
                threshold=f"{config.turnover.min_turnover*100}% ~ {config.turnover.max_turnover*100}%",
                conclusion="数据不足，无法计算平均换手率",
                is_passed=False,
            )

        # 使用配置的回看天数
        lookback_days = min(config.turnover.lookback_days, len(turnover_series))
        turnover_series = turnover_series[-lookback_days:]

        # 计算平均换手率
        avg_turnover = np.mean(turnover_series)

        # 使用配置的换手率阈值
        is_passed = (
            config.turnover.min_turnover <= avg_turnover <= config.turnover.max_turnover
        )
        conclusion = "换手率适中" if is_passed else "换手率过高或过低"

        return self.output_format(
            value=round(float(avg_turnover * 100), 2),
            threshold=f"{config.turnover.min_turnover*100}% ~ {config.turnover.max_turnover*100}%",
            conclusion=conclusion,
            is_passed=bool(is_passed),
        )
