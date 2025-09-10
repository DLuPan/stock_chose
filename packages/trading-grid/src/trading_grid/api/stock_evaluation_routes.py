"""
股票评估API路由
定义与股票评估相关的API端点
"""
from fastapi import APIRouter
from trading_grid.api.schemas.evaluation_result import EvaluationResult
from trading_grid.business.stock_evaluator import StockEvaluationService

router = APIRouter(prefix="/evaluate", tags=["股票评估"])

# 初始化业务服务
stock_evaluation_service = StockEvaluationService()


@router.get("/{symbol}", response_model=EvaluationResult)
async def evaluate_symbol(symbol: str):
    """
    评估指定股票是否适合网格交易
    
    Args:
        symbol: 股票代码
        
    Returns:
        EvaluationResult: 评估结果
    """
    # 调用业务服务处理
    return stock_evaluation_service.evaluate_symbol(symbol)