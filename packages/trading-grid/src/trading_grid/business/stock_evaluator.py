"""
股票评估业务逻辑处理
"""
from trading_grid.path import get_project_root
from trading_grid.evaluator import FactorEvaluator
from trading_grid.grid.generator import GridGenerator
from trading_grid.api.schemas.evaluation_result import EvaluationResult
from trading_grid.api.schemas.grid_config import GridConfig
import numpy as np
import pandas as pd
import os


class StockEvaluationService:
    """
    股票评估服务类
    处理股票评估的核心业务逻辑
    """

    def evaluate_symbol(self, symbol: str) -> EvaluationResult:
        """
        评估指定股票是否适合网格交易
        
        Args:
            symbol: 股票代码
            
        Returns:
            EvaluationResult: 评估结果
        """
        # 1. 获取历史数据
        price_series = self._get_price_series(symbol)
        pe_value = 25  # 假设市盈率

        # 2. 运行因子评估
        evaluator = FactorEvaluator(
            os.path.join(get_project_root(), "config/factors.yaml"), symbol
        )
        factors_results_list = evaluator.run(price_series=price_series, pe_value=pe_value)

        # 3. 分类因子结果
        reason = {"technical": [], "fundamental": [], "sentiment": []}
        for fr in factors_results_list:
            # 确保所有numpy类型都被转换为Python原生类型
            if isinstance(fr.get("is_passed"), np.bool_):
                fr["is_passed"] = bool(fr["is_passed"])
            if isinstance(fr.get("value"), np.integer):
                fr["value"] = int(fr["value"])
            elif isinstance(fr.get("value"), np.floating):
                fr["value"] = float(fr["value"])
                
            f_type = (
                "technical"
                if fr["factor"] in ["volatility", "volume"]
                else "fundamental" if fr["factor"] in ["pe_ratio"] else "sentiment"
            )
            reason[f_type].append(fr)

        # 4. 判断是否支持网格
        is_supported = all(f["is_passed"] for cat in reason.values() for f in cat)
        
        # 确保is_supported是Python原生bool类型
        is_supported = bool(is_supported)

        # 5. 生成网格配置（如果支持）
        grid_config = None
        if is_supported:
            current_price = price_series.iloc[-1]
            generator = GridGenerator(symbol, current_price=current_price)
            grid_config_data = generator.generate()
            grid_config = GridConfig(**grid_config_data)

        # 6. 返回结果
        return EvaluationResult(
            symbol=symbol, is_supported=is_supported, reason=reason, grid_config=grid_config
        )

    def _get_price_series(self, symbol: str, lookback_days: int = 180):
        """
        获取历史价格序列（模拟数据）
        
        Args:
            symbol: 股票代码
            lookback_days: 回看天数
            
        Returns:
            pd.Series: 价格序列
        """
        # 随机生成历史价格序列示例
        np.random.seed(0)
        base_price = 100.0
        returns = np.random.normal(0, 0.01, lookback_days)
        prices = base_price * (1 + pd.Series(returns)).cumprod()
        return prices