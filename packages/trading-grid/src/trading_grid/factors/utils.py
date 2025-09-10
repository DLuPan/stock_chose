# 因子自动注册装饰器
from trading_grid.factors.registry import FactorRegistry


def register_factor(cls):
    """类装饰器，用于自动注册因子"""
    FactorRegistry.register(cls)
    return cls
