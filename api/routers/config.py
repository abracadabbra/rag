"""
配置热更新路由
允许运行时动态调整部分配置（无需重启服务）
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException

from api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# 可热更新的配置项（键名 -> (类型, 描述)）
HOT_RELOADABLE_CONFIG = {
    "enable_rerank": (bool, "是否启用精排"),
    "rerank_top_k": (int, "精排返回数量"),
    "rerank_model": (str, "精排模型名称"),
    "enable_bm25": (bool, "是否启用 BM25 粗排"),
    "bm25_index_dir": (str, "BM25 索引目录"),
    "retrieval_top_k": (int, "检索返回数量"),
    "retrieval_score_threshold": (float, "检索分数阈值"),
    "cache_enabled": (bool, "是否启用缓存"),
    "cache_ttl": (int, "缓存 TTL（秒）"),
}

# 运行时配置覆盖（内存中的最新值）
_runtime_config: Dict[str, Any] = {}


def get_hot_config(key: str) -> Any:
    """获取配置值（运行时覆盖优先）"""
    if key in _runtime_config:
        return _runtime_config[key]
    return getattr(settings, key, None)


def set_hot_config(key: str, value: Any) -> None:
    """设置运行时配置覆盖"""
    _runtime_config[key] = value
    logger.info(f"配置热更新: {key} = {value}")


@router.get("/config", summary="获取热更新配置")
async def get_config() -> Dict[str, Any]:
    """
    获取所有可热更新的配置项及其当前值

    返回格式:
    {
        "enable_rerank": {"value": true, "type": "bool", "description": "...", "source": "runtime"},
        ...
    }
    """
    result = {}

    for key, (config_type, description) in HOT_RELOADABLE_CONFIG.items():
        current_value = get_hot_config(key)
        source = "runtime" if key in _runtime_config else "env"

        result[key] = {
            "value": current_value,
            "type": config_type.__name__,
            "description": description,
            "source": source
        }

    return result


@router.get("/config/{key}", summary="获取单个配置项")
async def get_config_item(key: str) -> Dict[str, Any]:
    """获取指定配置项的详细信息"""
    if key not in HOT_RELOADABLE_CONFIG:
        raise HTTPException(status_code=404, detail=f"配置项 '{key}' 不支持热更新")

    config_type, description = HOT_RELOADABLE_CONFIG[key]
    current_value = get_hot_config(key)
    source = "runtime" if key in _runtime_config else "env"

    return {
        "key": key,
        "value": current_value,
        "type": config_type.__name__,
        "description": description,
        "source": source
    }


@router.put("/config/{key}", summary="更新配置项")
async def update_config(key: str, value: Any) -> Dict[str, Any]:
    """
    更新热更新配置项

    请求体: 任意类型（根据配置项类型自动转换）

    示例:
    - PUT /api/v1/config/enable_rerank  body: true
    - PUT /api/v1/config/rerank_top_k   body: 5
    """
    if key not in HOT_RELOADABLE_CONFIG:
        raise HTTPException(status_code=404, detail=f"配置项 '{key}' 不支持热更新")

    config_type, description = HOT_RELOADABLE_CONFIG[key]

    # 类型校验和转换
    try:
        if config_type == bool:
            # 特殊处理布尔值
            if isinstance(value, bool):
                typed_value = value
            elif isinstance(value, str):
                typed_value = value.lower() in ("true", "1", "yes", "on")
            else:
                typed_value = bool(value)
        elif config_type == int:
            typed_value = int(value)
        elif config_type == float:
            typed_value = float(value)
        elif config_type == str:
            typed_value = str(value)
        else:
            typed_value = value
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"类型转换失败: {key} 期望 {config_type.__name__} 类型"
        )

    # 设置运行时覆盖
    set_hot_config(key, typed_value)

    logger.info(f"配置已热更新: {key} = {typed_value} (类型: {config_type.__name__})")

    return {
        "key": key,
        "value": typed_value,
        "type": config_type.__name__,
        "description": description,
        "source": "runtime"
    }


@router.delete("/config/{key}", summary="重置配置项")
async def reset_config(key: str) -> Dict[str, Any]:
    """
    重置配置项到环境变量默认值（移除运行时覆盖）
    """
    if key not in HOT_RELOADABLE_CONFIG:
        raise HTTPException(status_code=404, detail=f"配置项 '{key}' 不支持热更新")

    if key in _runtime_config:
        del _runtime_config[key]
        logger.info(f"配置已重置: {key}")

    default_value = getattr(settings, key, None)

    return {
        "key": key,
        "value": default_value,
        "type": HOT_RELOADABLE_CONFIG[key][0].__name__,
        "description": HOT_RELOADABLE_CONFIG[key][1],
        "source": "env"
    }


@router.post("/config/batch", summary="批量更新配置")
async def batch_update_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    批量更新多个配置项

    请求体:
    {
        "enable_rerank": true,
        "rerank_top_k": 5
    }
    """
    results = {}
    errors = []

    for key, value in updates.items():
        if key not in HOT_RELOADABLE_CONFIG:
            errors.append({"key": key, "error": "不支持热更新"})
            continue

        try:
            config_type, _ = HOT_RELOADABLE_CONFIG[key]

            # 类型转换
            if config_type == bool:
                if isinstance(value, bool):
                    typed_value = value
                elif isinstance(value, str):
                    typed_value = value.lower() in ("true", "1", "yes", "on")
                else:
                    typed_value = bool(value)
            elif config_type == int:
                typed_value = int(value)
            elif config_type == float:
                typed_value = float(value)
            else:
                typed_value = str(value)

            set_hot_config(key, typed_value)
            results[key] = typed_value

        except (ValueError, TypeError) as e:
            errors.append({"key": key, "error": str(e)})

    return {
        "updated": results,
        "errors": errors,
        "total_updated": len(results),
        "total_errors": len(errors)
    }
