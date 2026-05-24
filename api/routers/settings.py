"""
LLM API 设置路由
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.services.settings_service import get_llm_settings, update_llm_settings

router = APIRouter()

VALID_PROVIDERS = {"minimax", "openai", "local"}


class LlmSettingsUpdate(BaseModel):
    """LLM 配置更新请求体"""
    llm_provider: Optional[str] = None
    minimax_api_key: Optional[str] = None
    minimax_api_base: Optional[str] = None
    minimax_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_api_base: Optional[str] = None
    openai_model: Optional[str] = None
    openai_temperature: Optional[float] = Field(None, ge=0, le=2)
    openai_max_tokens: Optional[int] = Field(None, ge=1, le=32000)
    local_llm_base_url: Optional[str] = None
    local_llm_model: Optional[str] = None


@router.get("/", summary="获取 LLM 配置")
async def get_settings():
    """
    获取当前 LLM 配置（API key 等敏感字段已脱敏）
    """
    try:
        return get_llm_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取配置失败: {e}")


@router.patch("/", summary="更新 LLM 配置")
async def patch_settings(body: LlmSettingsUpdate):
    """
    更新 LLM 配置项，写入 .env 文件
    """
    updates = body.model_dump(exclude_none=True)

    if not updates:
        raise HTTPException(status_code=400, detail="未提供任何更新字段")

    if "llm_provider" in updates and updates["llm_provider"] not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=422,
            detail=f"无效的 llm_provider: {updates['llm_provider']}，可选值: {VALID_PROVIDERS}"
        )

    try:
        result = update_llm_settings(updates)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {e}")
