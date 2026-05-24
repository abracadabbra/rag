"""
LLM API 设置服务
读写 .env 文件中的 LLM 相关配置
"""

from __future__ import annotations

from pathlib import Path

ENV_FILE = Path(__file__).parent.parent.parent / ".env"


def _mask_api_key(key: str) -> str:
    """脱敏 API key，只显示前4位和后4位"""
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
        if "api_key" in key and value:
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
                env_vars[key] = value
                updated_keys.append(key)

    if updated_keys:
        _write_env(env_vars)

    return {"updated": updated_keys, "success": True}
