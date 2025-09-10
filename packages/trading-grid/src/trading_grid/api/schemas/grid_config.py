"""
网格配置数据模型
"""
from typing import List
from pydantic import BaseModel


class GridConfig(BaseModel):
    """
    网格配置模型
    """
    lower_bound: float
    upper_bound: float
    grid_count: int
    grid_spacing_mode: str
    grid_spacing_pct: float
    current_price: float
    grid_levels: List[float]