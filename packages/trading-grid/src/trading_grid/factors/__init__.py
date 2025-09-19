# 因子计算模块
# 为了确保装饰器 @register_factor 能够正确执行，需要在这里导入所有因子类
from .volatility import VolatilityFactor
from .pe_ratio import PeRatioFactor
from .volume import VolumeFactor
from .trend import TrendFactor
from .price_range import PriceRangeFactor
from .market_cap import MarketCapFactor
from .turnover import TurnoverFactor