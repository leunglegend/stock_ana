"""
FastAPI 主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.models import User, WatchlistGroup, WatchlistItem  # noqa: F401  确保模型被导入以建表
from app.routes.stock import router as stock_router
from app.routes.board import router as board_router
from app.routes.auth import router as auth_router
from app.routes.watchlist import router as watchlist_router

app = FastAPI(
    title="股票分析 API",
    description="基于 AKShare 和大模型的股票分析后端服务",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(stock_router)
app.include_router(board_router)
app.include_router(auth_router)
app.include_router(watchlist_router)


@app.on_event("startup")
async def preload_data():
    """启动时建表并预加载所有缓存数据（后台异步，不阻塞启动）"""
    # 创建所有数据表
    Base.metadata.create_all(bind=engine)

    """启动时预加载所有缓存数据（后台异步，不阻塞启动）"""
    import asyncio

    def _load():
        try:
            from app.services.stock_data import _get_stock_list
            stocks = _get_stock_list()
            print(f"预加载股票列表完成，共 {len(stocks)} 只")
        except Exception as e:
            print(f"预加载股票列表失败: {e}")

        # 启动市场数据定时刷新
        try:
            from app.services.data_cache import start_cache_refresh
            start_cache_refresh()
        except Exception as e:
            print(f"启动缓存刷新失败: {e}")

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _load)


@app.get("/", summary="健康检查")
async def root():
    return {
        "status": "ok",
        "service": "股票分析 API",
        "ai_available": settings.ai_available,
    }


@app.get("/health", summary="健康检查")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
