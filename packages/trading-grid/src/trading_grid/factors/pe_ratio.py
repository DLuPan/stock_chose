import pandas as pd
from trading_grid.factors.base import BaseFactor
from trading_grid.factors.utils import register_factor
from trading_grid.factors.factor_config import config


@register_factor
class PeRatioFactor(BaseFactor):
    factor_name = "pe_ratio"
    factor_cn_name = "市盈率"

    def calculate(self, pe_value: float = None, price_series: pd.Series = None) -> dict:
        if pe_value is None:
            return self.output_format(
                value=None,
                threshold=f"< {config.pe_ratio.max_pe}",
                conclusion="缺少市盈率数据",
                is_passed=False,
            )

        is_passed = pe_value < config.pe_ratio.max_pe
        conclusion = "估值合理" if is_passed else "估值过高"

        return self.output_format(
            value=round(float(pe_value), 2),
            threshold=f"< {config.pe_ratio.max_pe}",
            conclusion=conclusion,
            is_passed=bool(is_passed),
        )
