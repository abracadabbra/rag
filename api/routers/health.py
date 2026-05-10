"""
健康检查路由
"""

from fastapi import APIRouter, status
from datetime import datetime
from api.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """
    综合健康检查

    检查所有依赖服务的状态
    """
    checks = {
        "api": {"status": "healthy"},
        "milvus": await _check_milvus(),
        "redis": await _check_redis(),
        "openai": await _check_openai()
    }

    # 判断整体状态
    all_healthy = all(
        check["status"] == "healthy"
        for check in checks.values()
    )

    overall_status = "healthy" if all_healthy else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": checks
    }


async def _check_milvus() -> dict:
    """检查 Milvus 连接"""
    try:
        from pymilvus import connections, utility

        connections.connect(
            alias="health_check",
            host=settings.milvus_host,
            port=settings.milvus_port
        )

        # 检查 Collection 是否存在
        has_collection = utility.has_collection(settings.milvus_collection)

        connections.disconnect("health_check")

        return {
            "status": "healthy",
            "host": settings.milvus_host,
            "port": settings.milvus_port,
            "collection_exists": has_collection
        }
    except Exception as e:
        logger.error(f"Milvus 健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _check_redis() -> dict:
    """检查 Redis 连接"""
    try:
        import redis

        r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password if settings.redis_password else None,
            db=settings.redis_db,
            socket_connect_timeout=2
        )

        # 测试连接
        r.ping()
        r.close()

        return {
            "status": "healthy",
            "host": settings.redis_host,
            "port": settings.redis_port
        }
    except Exception as e:
        logger.error(f"Redis 健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _check_openai() -> dict:
    """检查 OpenAI API 可用性"""
    try:
        from openai import OpenAI

        if not settings.openai_api_key:
            return {
                "status": "not_configured",
                "message": "OpenAI API Key 未配置"
            }

        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
            timeout=5.0
        )

        # 简单测试：列出模型
        models = client.models.list()

        return {
            "status": "healthy",
            "model": settings.openai_model,
            "base_url": settings.openai_api_base
        }
    except Exception as e:
        logger.error(f"OpenAI 健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/health/milvus")
async def milvus_health():
    """Milvus 独立健康检查"""
    return await _check_milvus()


@router.get("/health/redis")
async def redis_health():
    """Redis 独立健康检查"""
    return await _check_redis()


@router.get("/health/openai")
async def openai_health():
    """OpenAI 独立健康检查"""
    return await _check_openai()
