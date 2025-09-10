# 因子计算的基础
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseFactor(ABC):
    """
    抽象父类，所有因子必须继承并实现 calculate 方法
    """

    def __init__(self, symbol: str, lookback_days: int = 180):
        self.symbol = symbol
        self.lookback_days = lookback_days

    @property
    @abstractmethod
    def factor_name(self) -> str:
        """因子英文名（程序用），如 'volatility'"""
        pass

    @property
    @abstractmethod
    def factor_cn_name(self) -> str:
        """因子中文名（展示用），如 '波动率'"""
        pass

    @abstractmethod
    def calculate(self, **kwargs) -> Dict[str, Any]:
        """
        子类必须实现该方法，返回统一格式的结果字典
        """
        pass

    def output_format(
        self, value: Any, threshold: Any, conclusion: str, is_passed: bool
    ) -> Dict[str, Any]:
        """
        通用输出格式，所有因子都应通过该方法返回结果
        """
        return {
            "factor": self.factor_name,
            "name": self.factor_cn_name,
            "value": value,
            "threshold": threshold,
            "conclusion": conclusion,
            "is_passed": bool(is_passed),  # 确保转换为Python原生bool类型
        }