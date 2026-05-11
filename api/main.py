"""
FastAPI 主应用入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.logging_config import setup_logging
from api.routers.cache import router as cache_router
from api.routers.health import router as health_router
from api.routers.risk_rules import router as risk_rules_router
from api.routers.model_cards import router as model_cards_router
from api.routers.simulation import router as simulation_router
from api.routers.profit import router as profit_router

# 初始化日志
setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print(f"🚀 {settings.app_name} v{settings.app_version} 启动中...")
    print(f"   环境: {settings.environment}")
    print(f"   Milvus: {settings.milvus_host}:{settings.milvus_port}")
    print(f"   Redis: {settings.redis_host}:{settings.redis_port}")

    yield

    # 关闭时执行
    print(f"👋 {settings.app_name} 关闭中...")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="统一 RAG 技术架构系统 - 支持多场景智能问答",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health_router, tags=["健康检查"])
app.include_router(risk_rules_router, prefix="/api/v1/risk-rules", tags=["风控规则"])
app.include_router(model_cards_router, prefix="/api/v1/model-cards", tags=["模型卡片"])
app.include_router(simulation_router, prefix="/api/v1/simulation", tags=["仿真解读"])
app.include_router(profit_router, prefix="/api/v1/profit", tags=["毛利抽成"])
app.include_router(cache_router, prefix="/api/v1/cache", tags=["缓存管理"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=1 if settings.api_reload else settings.api_workers
    )
