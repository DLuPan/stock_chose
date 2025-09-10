import yaml
import numpy as np
from trading_grid.factors.registry import FactorRegistry
from trading_grid.logger import log


class FactorEvaluator:
    def __init__(self, config_path: str, symbol: str):
        self.symbol = symbol
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def run(self, **kwargs):
        log.info(f"开始评估股票 {self.symbol} 的因子")
        results = []
        for factor_name in self.config["factors"]:
            log.info(f"正在评估因子 {factor_name}...")
            factor_cls = FactorRegistry.get(factor_name)
            if factor_cls is None:
                log.warning(f"因子 {factor_name} 未注册，跳过评估")
                results.append(
                    {
                        "factor": factor_name,
                        "name": "未知因子",
                        "value": None,
                        "threshold": None,
                        "conclusion": "未注册的因子",
                        "is_passed": False,
                    }
                )
                continue

            factor = factor_cls(self.symbol)
            result = factor.calculate(**kwargs)
            
            # 确保所有numpy类型都被转换为Python原生类型
            if isinstance(result.get("is_passed"), np.bool_):
                result["is_passed"] = bool(result["is_passed"])
            if isinstance(result.get("value"), np.integer):
                result["value"] = int(result["value"])
            elif isinstance(result.get("value"), np.floating):
                result["value"] = float(result["value"])
                
            results.append(result)
            log.info(f"因子 {factor_name} 评估完成，结果: {result}")

        log.info(f"股票 {self.symbol} 的因子评估完成，共评估 {len(results)} 个因子")
        return results