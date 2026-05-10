"""
缓存管理路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from api.services.cache_service import get_cache_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class CacheStatsResponse(BaseModel):
    """缓存统计响应"""
    enabled: bool
    total_keys: int
    memory_used_bytes: Optional[int] = None
    memory_used_human: Optional[str] = None
    ttl: Optional[int] = None
    error: Optional[str] = None


class CacheInvalidateRequest(BaseModel):
    """缓存清除请求"""
    pattern: Optional[str] = None
    scene_type: Optional[str] = None


class CacheInvalidateResponse(BaseModel):
    """缓存清除响应"""
    deleted_count: int
    message: str


@router.get(
    "/stats",
    response_model=CacheStatsResponse,
    summary="获取缓存统计",
    description="获取缓存使用情况统计信息"
)
async def get_cache_stats():
    """
    获取缓存统计信息

    返回：
    - enabled: 缓存是否启用
    - total_keys: 缓存 key 总数
    - memory_used_bytes: 内存使用量（字节）
    - memory_used_human: 内存使用量（人类可读）
    - ttl: 缓存过期时间（秒）
    """
    try:
        cache_service = get_cache_service()
        stats = cache_service.get_stats()
        return CacheStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取缓存统计失败: {str(e)}"
        )


@router.post(
    "/invalidate",
    response_model=CacheInvalidateResponse,
    summary="清除缓存",
    description="清除指定模式或场景的缓存"
)
async def invalidate_cache(request: CacheInvalidateRequest):
    """
    清除缓存

    请求参数：
    - pattern: 缓存 key 模式（如 "rag:query:*"）
    - scene_type: 场景类型（如 "risk_rule"）

    如果两个参数都不提供，则清除所有查询缓存。
    """
    try:
        cache_service = get_cache_service()

        if request.pattern:
            deleted = cache_service.invalidate(pattern=request.pattern)
            message = f"已清除匹配模式 '{request.pattern}' 的缓存"
        elif request.scene_type:
            deleted = cache_service.invalidate(scene_type=request.scene_type)
            message = f"已清除场景 '{request.scene_type}' 的缓存"
        else:
            deleted = cache_service.invalidate(pattern="rag:query:*")
            message = "已清除所有查询缓存"

        logger.info(f"缓存清除成功 - 删除 {deleted} 个 key")

        return CacheInvalidateResponse(
            deleted_count=deleted,
            message=message
        )

    except Exception as e:
        logger.error(f"清除缓存失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"清除缓存失败: {str(e)}"
        )


@router.delete(
    "/clear",
    response_model=CacheInvalidateResponse,
    summary="清空所有缓存",
    description="清空所有查询缓存（危险操作）"
)
async def clear_all_cache():
    """
    清空所有查询缓存

    ⚠️ 危险操作：会清除所有查询缓存
    """
    try:
        cache_service = get_cache_service()
        deleted = cache_service.invalidate(pattern="rag:query:*")

        logger.warning(f"清空所有缓存 - 删除 {deleted} 个 key")

        return CacheInvalidateResponse(
            deleted_count=deleted,
            message=f"已清空所有查询缓存，共删除 {deleted} 个 key"
        )

    except Exception as e:
        logger.error(f"清空缓存失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"清空缓存失败: {str(e)}"
        )
