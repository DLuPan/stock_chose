# 实现因子的动态注册
from typing import Dict, Type
from trading_grid.factors.base import BaseFactor


class FactorRegistry:
    """
    因子注册中心
    用于统一管理、动态加载因子
    """

    _registry: Dict[str, Type[BaseFactor]] = {}

    @classmethod
    def register(cls, factor_cls: Type[BaseFactor]):
        """注册因子类"""
        if not issubclass(factor_cls, BaseFactor):
            raise TypeError("因子必须继承 BaseFactor")
        cls._registry[factor_cls.factor_name] = factor_cls

    @classmethod
    def get(cls, name: str) -> Type[BaseFactor]:
        """根据名称获取因子类"""
        return cls._registry.get(name)

    @classmethod
    def all(cls) -> Dict[str, Type[BaseFactor]]:
        """获取所有注册的因子"""
        return cls._registry
