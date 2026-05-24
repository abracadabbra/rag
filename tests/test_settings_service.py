"""
Settings 服务单元测试
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from api.services.settings_service import (
    _mask_api_key,
    _read_env,
    _write_env,
    get_llm_settings,
    update_llm_settings,
    LLM_CONFIG_KEYS,
)


@pytest.fixture
def temp_env(tmp_path):
    """创建临时 .env 文件并 patch ENV_FILE 路径"""
    env_file = tmp_path / ".env"
    with patch("api.services.settings_service.ENV_FILE", env_file):
        yield env_file


class TestMaskApiKey:
    """API Key 脱敏测试"""

    def test_short_key(self):
        assert _mask_api_key("abc") == "****"

    def test_exactly_8_chars(self):
        assert _mask_api_key("12345678") == "****"

    def test_long_key(self):
        result = _mask_api_key("sk-1234567890abcdef")
        assert result == "sk-1****cdef"

    def test_empty_key(self):
        assert _mask_api_key("") == "****"

    def test_none_key(self):
        assert _mask_api_key(None) == "****"


class TestReadEnv:
    """读取 .env 测试"""

    def test_read_nonexistent(self, temp_env):
        assert _read_env() == {}

    def test_read_basic(self, temp_env):
        temp_env.write_text("llm_provider=minimax\nminimax_api_key=sk-test123\n")
        result = _read_env()
        assert result["llm_provider"] == "minimax"
        assert result["minimax_api_key"] == "sk-test123"

    def test_read_quoted_values(self, temp_env):
        temp_env.write_text('API_KEY="sk-test"\nAPI_BASE=\'http://localhost\'\n')
        result = _read_env()
        assert result["API_KEY"] == "sk-test"
        assert result["API_BASE"] == "http://localhost"

    def test_skip_comments_and_blanks(self, temp_env):
        temp_env.write_text("# comment\n\nKEY=value\n# another\n")
        result = _read_env()
        assert result == {"KEY": "value"}


class TestWriteEnv:
    """写入 .env 测试"""

    def test_write_new_file(self, temp_env):
        _write_env({"KEY1": "val1", "KEY2": "val2"})
        content = temp_env.read_text()
        assert "KEY1=val1" in content
        assert "KEY2=val2" in content

    def test_write_updates_existing(self, temp_env):
        temp_env.write_text("KEY1=old\nKEY2=keep\n")
        _write_env({"KEY1": "new"})
        result = _read_env_from_file(temp_env)
        assert result["KEY1"] == "new"
        assert result["KEY2"] == "keep"

    def test_write_preserves_comments(self, temp_env):
        temp_env.write_text("# comment\nKEY1=old\n")
        _write_env({"KEY1": "new"})
        content = temp_env.read_text()
        assert "# comment" in content
        assert "KEY1=new" in content

    def test_write_appends_new_keys(self, temp_env):
        temp_env.write_text("EXISTING=value\n")
        _write_env({"NEW_KEY": "new_val"})
        result = _read_env_from_file(temp_env)
        assert result["EXISTING"] == "value"
        assert result["NEW_KEY"] == "new_val"


def _read_env_from_file(path):
    """辅助函数：从文件读取 env"""
    env_vars = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars


class TestGetLlmSettings:
    """获取 LLM 配置测试"""

    def test_empty_env(self, temp_env):
        result = get_llm_settings()
        for key in LLM_CONFIG_KEYS:
            assert key in result
            assert result[key] == ""

    def test_api_key_masked(self, temp_env):
        temp_env.write_text("minimax_api_key=sk-1234567890\n")
        result = get_llm_settings()
        assert result["minimax_api_key"] == "sk-1****7890"

    def test_non_key_fields_not_masked(self, temp_env):
        temp_env.write_text("minimax_model=MiniMax-M2.7\n")
        result = get_llm_settings()
        assert result["minimax_model"] == "MiniMax-M2.7"


class TestUpdateLlmSettings:
    """更新 LLM 配置测试"""

    def test_update_single_field(self, temp_env):
        result = update_llm_settings({"llm_provider": "openai"})
        assert result["success"] is True
        assert "llm_provider" in result["updated"]

        settings = get_llm_settings()
        assert settings["llm_provider"] == "openai"

    def test_update_ignores_unknown_keys(self, temp_env):
        result = update_llm_settings({"unknown_key": "value", "llm_provider": "local"})
        assert result["success"] is True
        assert "unknown_key" not in result["updated"]
        assert "llm_provider" in result["updated"]

    def test_update_none_value_skipped(self, temp_env):
        result = update_llm_settings({"llm_provider": None})
        assert result["updated"] == []

    def test_update_multiple_fields(self, temp_env):
        result = update_llm_settings({
            "llm_provider": "minimax",
            "minimax_model": "test-model",
        })
        assert len(result["updated"]) == 2
