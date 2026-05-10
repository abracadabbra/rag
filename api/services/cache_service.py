"""
Query 缓存服务
使用 Redis 缓存查询结果，降低成本和延迟
"""

import hashlib
import json
import logging
from typing import Optional, Dict, Any

try:
    from redis import Redis
except ModuleNotFoundError:  # pragma: no cover - 仅在依赖未安装的轻量环境触发
    Redis = Any
from api.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """缓存服务"""

    def __init__(self, redis_client: Redis = None, ttl: int = 3600):
        """
        初始化缓存服务

        Args:
            redis_client: Redis 客户端
            ttl: 缓存过期时间（秒），默认 1 小时
        """
        self.redis = redis_client
        self.ttl = ttl
        self.enabled = settings.cache_enabled
        logger.info(f"缓存服务初始化 - enabled: {self.enabled}, ttl: {ttl}s")

    def _generate_cache_key(
        self,
        query: str,
        scene_type: str,
        top_k: int,
        score_threshold: float
    ) -> str:
        """
        生成缓存 key

        Args:
            query: 用户问题
            scene_type: 场景类型
            top_k: 返回文档数量
            score_threshold: 相似度阈值

        Returns:
            缓存 key
        """
        # 将查询参数组合成字符串
        cache_str = f"{scene_type}:{query}:{top_k}:{score_threshold}"

        # 使用 MD5 生成短 key
        cache_hash = hashlib.md5(cache_str.encode('utf-8')).hexdigest()

        return f"rag:query:{scene_type}:{cache_hash}"

    def get(
        self,
        query: str,
        scene_type: str,
        top_k: int,
        score_threshold: float
    ) -> Optional[Dict[str, Any]]:
        """
        从缓存获取查询结果

        Args:
            query: 用户问题
            scene_type: 场景类型
            top_k: 返回文档数量
            score_threshold: 相似度阈值

        Returns:
            缓存的查询结果，如果不存在则返回 None
        """
        if not self.enabled or not self.redis:
            return None

        try:
            cache_key = self._generate_cache_key(query, scene_type, top_k, score_threshold)
            cached_data = self.redis.get(cache_key)

            if cached_data:
                result = json.loads(cached_data)
                logger.info(f"缓存命中 - key: {cache_key[:16]}...")
                return result
            else:
                logger.debug(f"缓存未命中 - key: {cache_key[:16]}...")
                return None

        except Exception as e:
            logger.error(f"缓存读取失败: {e}")
            return None

    def set(
        self,
        query: str,
        scene_type: str,
        top_k: int,
        score_threshold: float,
        result: Dict[str, Any]
    ) -> bool:
        """
        将查询结果写入缓存

        Args:
            query: 用户问题
            scene_type: 场景类型
            top_k: 返回文档数量
            score_threshold: 相似度阈值
            result: 查询结果

        Returns:
            是否写入成功
        """
        if not self.enabled or not self.redis:
            return False

        try:
            cache_key = self._generate_cache_key(query, scene_type, top_k, score_threshold)

            # 序列化结果
            cached_data = json.dumps(result, ensure_ascii=False)

            # 写入 Redis，设置过期时间
            self.redis.setex(cache_key, self.ttl, cached_data)

            logger.debug(f"缓存写入成功 - key: {cache_key[:16]}..., ttl: {self.ttl}s")
            return True

        except Exception as e:
            logger.error(f"缓存写入失败: {e}")
            return False

    def invalidate(
        self,
        query: str = None,
        scene_type: str = None,
        pattern: str = None
    ) -> int:
        """
        清除缓存

        Args:
            query: 用户问题（可选）
            scene_type: 场景类型（可选）
            pattern: 缓存 key 模式（可选，如 "rag:query:*"）

        Returns:
            清除的缓存数量
        """
        if not self.enabled or not self.redis:
            return 0

        try:
            if pattern:
                keys = self.redis.keys(pattern)
            elif scene_type:
                keys = self.redis.keys(f"rag:query:{scene_type}:*")
            else:
                keys = self.redis.keys("rag:query:*")

            if query and scene_type and keys:
                logger.warning(
                    "query 级缓存失效未实现精确匹配，已回退为按 scene_type 清理 - scene_type: %s",
                    scene_type,
                )

            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"缓存清除成功 - 删除 {deleted} 个 key")
                return deleted
            else:
                logger.debug("没有找到需要清除的缓存")
                return 0

        except Exception as e:
            logger.error(f"缓存清除失败: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息
        """
        if not self.enabled or not self.redis:
            return {
                "enabled": False,
                "total_keys": 0,
                "memory_used": 0
            }

        try:
            # 获取所有查询缓存 key
            keys = self.redis.keys("rag:query:*")

            # 获取 Redis 内存使用情况
            info = self.redis.info("memory")

            return {
                "enabled": True,
                "total_keys": len(keys),
                "memory_used_bytes": info.get("used_memory", 0),
                "memory_used_human": info.get("used_memory_human", "0B"),
                "ttl": self.ttl
            }

        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {
                "enabled": True,
                "error": str(e)
            }


# 全局单例
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """获取缓存服务单例"""
    global _cache_service
    if _cache_service is None:
        from api.services.session_manager import get_redis_client
        redis_client = get_redis_client()
        _cache_service = CacheService(
            redis_client=redis_client,
            ttl=settings.cache_ttl
        )
    return _cache_service
