from typing import List, Dict, Any, Optional, Union
from pathlib import Path

import yaml
import numpy as np
import pandas as pd

from trading_grid.factors.registry import FactorRegistry
from trading_grid.factors.factor_config import FactorConfig, config as default_config
from trading_grid.logger import log


class EvaluationResult:
    """评估结果封装类"""

    def __init__(self, results: List[Dict[str, Any]], symbol: str):
        self.results = results
        self.symbol = symbol
        self._passed_factors = [r for r in results if r["is_passed"]]
        self._failed_factors = [r for r in results if not r["is_passed"]]

    @property
    def total_factors(self) -> int:
        """评估的因子总数"""
        return len(self.results)

    @property
    def passed_count(self) -> int:
        """通过的因子数量"""
        return len(self._passed_factors)

    @property
    def failed_count(self) -> int:
        """未通过的因子数量"""
        return len(self._failed_factors)

    @property
    def pass_rate(self) -> float:
        """通过率"""
        return self.passed_count / self.total_factors if self.total_factors > 0 else 0.0

    def get_factor_result(self, factor_name: str) -> Optional[Dict[str, Any]]:
        """获取指定因子的评估结果"""
        for result in self.results:
            if result["factor"] == factor_name:
                return result
        return None

    def to_dataframe(self) -> pd.DataFrame:
        """转换为DataFrame格式"""
        return pd.DataFrame(self.results)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "symbol": self.symbol,
            "total_factors": self.total_factors,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "pass_rate": self.pass_rate,
            "results": self.results,
        }

    def get_summary(self) -> str:
        """获取评估结果摘要"""
        return (
            f"股票{self.symbol}评估结果：\n"
            f"总计评估{self.total_factors}个因子\n"
            f"通过{self.passed_count}个，未通过{self.failed_count}个\n"
            f"通过率：{self.pass_rate:.2%}"
        )

    def __str__(self) -> str:
        return self.get_summary()


class FactorEvaluator:
    """因子评估器"""

    def __init__(
        self, symbol: str, config: Optional[Union[str, Path, FactorConfig]] = None
    ):
        """
        初始化评估器

        Args:
            symbol: 股票代码
            config: 配置来源，可以是：
                   - 配置文件路径（字符串或Path对象）
                   - FactorConfig对象
                   - None（使用默认配置）
        """
        self.symbol = symbol

        if isinstance(config, (str, Path)):
            self.config = FactorConfig.load_from_file(config)
        elif isinstance(config, FactorConfig):
            self.config = config
        elif config is None:
            self.config = default_config
        else:
            raise TypeError(f"不支持的配置类型：{type(config)}")

    def evaluate_factor(self, factor_name: str, **kwargs) -> Dict[str, Any]:
        """
        评估单个因子

        Args:
            factor_name: 因子名称
            **kwargs: 传递给因子计算方法的参数

        Returns:
            Dict[str, Any]: 因子评估结果
        """
        log.info(f"正在评估因子 {factor_name}...")

        # 检查因子是否启用
        if not self.config.is_factor_enabled(factor_name):
            log.info(f"因子 {factor_name} 未启用，跳过评估")
            return {
                "factor": factor_name,
                "name": "未启用因子",
                "value": None,
                "threshold": None,
                "conclusion": "因子未启用",
                "is_passed": False,
            }

        # 获取因子类
        factor_cls = FactorRegistry.get(factor_name)
        if factor_cls is None:
            log.warning(f"因子 {factor_name} 未注册，跳过评估")
            return {
                "factor": factor_name,
                "name": "未知因子",
                "value": None,
                "threshold": None,
                "conclusion": "未注册的因子",
                "is_passed": False,
            }

        # 实例化并计算
        factor = factor_cls(self.symbol)
        result = factor.calculate(**kwargs)

        # 转换numpy类型为Python原生类型
        if isinstance(result.get("is_passed"), np.bool_):
            result["is_passed"] = bool(result["is_passed"])
        if isinstance(result.get("value"), (np.integer, np.floating)):
            result["value"] = float(result["value"])

        log.info(f"因子 {factor_name} 评估完成，结果: {result}")
        return result

    def run(self, **kwargs) -> EvaluationResult:
        """
        运行所有启用的因子评估

        Args:
            **kwargs: 传递给各个因子的计算参数

        Returns:
            EvaluationResult: 评估结果对象
        """
        log.info(f"开始评估股票 {self.symbol} 的因子")
        results = []

        # 评估所有启用的因子
        for factor_name in self.config.enabled_factors:
            result = self.evaluate_factor(factor_name, **kwargs)
            results.append(result)

        # 创建评估结果对象
        evaluation_result = EvaluationResult(results, self.symbol)
        log.info(f"\n{evaluation_result.get_summary()}")

        return evaluation_result
