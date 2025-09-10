"""
因子评估结果数据模型
"""
from typing import Optional
from pydantic import BaseModel


class FactorResult(BaseModel):
    """
    因子评估结果模型
    """
    factor: str
    name: str
    value: Optional[float] = None
    threshold: Optional[str] = None
    conclusion: str
    is_passed: bool