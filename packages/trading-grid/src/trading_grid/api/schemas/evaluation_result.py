"""
评估结果数据模型
"""
from typing import Dict, List, Optional, Union
from pydantic import BaseModel
from trading_grid.api.schemas.factor_result import FactorResult
from trading_grid.api.schemas.grid_config import GridConfig


class EvaluationResult(BaseModel):
    """
    股票评估结果模型
    """
    symbol: str
    is_supported: bool
    reason: Dict[str, List[FactorResult]]  # technical / fundamental / sentiment: List[FactorResult]
    grid_config: Optional[GridConfig] = None