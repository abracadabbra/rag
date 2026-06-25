"""
LLM API 设置服务
读写 .env 文件中的 LLM 相关配置
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ENV_FILE = Path(__file__).parent.parent.parent / ".env"


def _mask_api_key(key: str | None) -> str:
    """脱敏 API key/token，只显示前4位和后4位"""
    if not key or len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _read_env() -> dict[str, str]:
    """读取当前 .env 文件内容为字典"""
    if not ENV_FILE.exists():
        return {}
    env_vars = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars


def _write_env(env_vars: dict[str, str]) -> None:
    """写入 .env 文件"""
    lines = []
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text().splitlines()

    existing_keys = set()
    new_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        if "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in env_vars:
                existing_keys.add(key)
                new_lines.append(f'{key}={env_vars[key]}')
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    for key, value in env_vars.items():
        if key not in existing_keys:
            new_lines.append(f'{key}={value}')

    ENV_FILE.write_text("\n".join(new_lines) + "\n")


def _format_env_value(value) -> str:
    """Format values consistently before writing them to .env."""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _is_secret_key(key: str) -> bool:
    """Return whether an env setting should be masked before display."""
    normalized_key = key.lower()
    return (
        "api_key" in normalized_key
        or normalized_key.endswith("_token")
        or normalized_key.endswith("_secret")
    )


LLM_CONFIG_KEYS = {
    "llm_provider",
    "minimax_api_key",
    "minimax_api_base",
    "minimax_model",
    "openai_api_key",
    "openai_api_base",
    "openai_model",
    "openai_temperature",
    "openai_max_tokens",
    "local_llm_enabled",
    "local_llm_base_url",
    "local_llm_model",
    "enable_business_tools",
    "business_tool_timeout",
    "enable_business_tool_llm_intent",
    "business_tool_llm_intent_min_confidence",
    "enable_business_tool_access_control",
    "business_tool_access_token",
    "business_tool_read_token",
    "business_tool_execute_token",
    "enable_business_tool_audit_file",
    "business_tool_audit_file",
    "risk_api_base_url",
    "risk_api_key",
    "profit_api_base_url",
    "profit_api_key",
}

BUSINESS_TOOL_CONFIG_KEYS = {
    "enable_business_tools",
    "business_tool_timeout",
    "enable_business_tool_llm_intent",
    "business_tool_llm_intent_min_confidence",
    "enable_business_tool_access_control",
    "business_tool_access_token",
    "business_tool_read_token",
    "business_tool_execute_token",
    "enable_business_tool_audit_file",
    "business_tool_audit_file",
    "risk_api_base_url",
    "risk_api_key",
    "profit_api_base_url",
    "profit_api_key",
}


def get_llm_settings() -> dict:
    """
    获取当前 LLM 配置
    敏感字段（api_key）做脱敏处理
    """
    env_vars = _read_env()

    result = {}
    for key in LLM_CONFIG_KEYS:
        value = env_vars.get(key, "")
        if _is_secret_key(key) and value:
            result[key] = _mask_api_key(value)
        else:
            result[key] = value

    return result


def update_llm_settings(updates: dict) -> dict:
    """
    更新 LLM 配置（只更新提供的字段）
    写入 .env 文件
    """
    env_vars = _read_env()

    updated_keys = []
    for key, value in updates.items():
        if key in LLM_CONFIG_KEYS:
            if value is not None:
                env_vars[key] = _format_env_value(value)
                updated_keys.append(key)

    if updated_keys:
        _write_env(env_vars)
        _apply_runtime_settings({key: env_vars[key] for key in updated_keys})
        if BUSINESS_TOOL_CONFIG_KEYS.intersection(updated_keys):
            _reset_business_tool_runtime()

    return {"updated": updated_keys, "success": True}


def _apply_runtime_settings(updates: dict[str, str]) -> None:
    """Apply settings changes to the in-process settings singleton."""
    from api.config import settings

    for key, value in updates.items():
        if not hasattr(settings, key):
            continue
        current_value = getattr(settings, key)
        setattr(settings, key, _cast_runtime_value(value, current_value))


def _cast_runtime_value(value: str, current_value: Any) -> Any:
    if isinstance(current_value, bool):
        return str(value).lower() == "true"
    if isinstance(current_value, int) and not isinstance(current_value, bool):
        return int(value)
    if isinstance(current_value, float):
        return float(value)
    return value


def _reset_business_tool_runtime() -> None:
    """Rebuild business clients/tool service after runtime business config changes."""
    from api.services.business_clients import reset_business_clients
    from api.services.tool_service import reset_tool_service

    reset_business_clients()
    reset_tool_service()

    try:
        from api.services.conversation_agent import reset_conversation_agent

        reset_conversation_agent()
    except ImportError:
        pass
