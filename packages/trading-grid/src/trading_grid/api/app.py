"""
FastAPI应用入口
"""
from fastapi import FastAPI
from trading_grid.api.stock_evaluation_routes import router as stock_evaluation_router


def create_app() -> FastAPI:
    """
    创建并配置FastAPI应用
    
    Returns:
        FastAPI: 配置好的FastAPI应用实例
    """
    app = FastAPI(
        title="Grid Trading Evaluation API",
        description="网格交易评估服务API",
        version="0.1.0"
    )
    
    # 注册路由
    app.include_router(stock_evaluation_router)
    
    return app


# 创建应用实例
app = create_app()