"""
Settings 服务单元测试
"""

import pytest
import sys
from types import SimpleNamespace
from unittest.mock import patch

from api.services.settings_service import (
    _is_secret_key,
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


@pytest.fixture(autouse=True)
def restore_business_tool_runtime_settings():
    """Avoid leaking runtime business-tool settings across tests."""
    from api.config import settings

    business_fields = [
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
    ]
    original_values = {field: getattr(settings, field) for field in business_fields}
    yield
    for field, value in original_values.items():
        setattr(settings, field, value)
    from api.services.business_clients import reset_business_clients
    from api.services.tool_service import reset_tool_service

    reset_business_clients()
    reset_tool_service()


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

    @pytest.mark.parametrize(
        "key",
        [
            "openai_api_key",
            "business_tool_access_token",
            "jwt_secret",
        ],
    )
    def test_secret_key_detection(self, key):
        assert _is_secret_key(key) is True

    def test_non_secret_key_detection(self):
        assert _is_secret_key("risk_api_base_url") is False


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
        temp_env.write_text(
            "minimax_api_key=sk-1234567890\n"
            "risk_api_key=risk-secret-123456\n"
            "profit_api_key=profit-secret-123456\n"
        )
        result = get_llm_settings()
        assert result["minimax_api_key"] == "sk-1****7890"
        assert result["risk_api_key"] == "risk****3456"
        assert result["profit_api_key"] == "prof****3456"

    def test_non_key_fields_not_masked(self, temp_env):
        temp_env.write_text("minimax_model=MiniMax-M2.7\n")
        result = get_llm_settings()
        assert result["minimax_model"] == "MiniMax-M2.7"

    def test_business_tool_intent_fields_are_exposed(self, temp_env):
        temp_env.write_text(
            "enable_business_tools=true\n"
            "business_tool_timeout=7\n"
            "enable_business_tool_llm_intent=true\n"
            "business_tool_llm_intent_min_confidence=0.8\n"
            "enable_business_tool_access_control=true\n"
            "business_tool_access_token=business-token-123456\n"
            "business_tool_read_token=read-token-123456\n"
            "business_tool_execute_token=execute-token-123456\n"
            "enable_business_tool_audit_file=true\n"
            "business_tool_audit_file=logs/business_tool_audit.jsonl\n"
            "risk_api_base_url=https://risk.example.test\n"
            "profit_api_base_url=https://profit.example.test\n"
        )

        result = get_llm_settings()

        assert result["enable_business_tools"] == "true"
        assert result["business_tool_timeout"] == "7"
        assert result["enable_business_tool_llm_intent"] == "true"
        assert result["business_tool_llm_intent_min_confidence"] == "0.8"
        assert result["enable_business_tool_access_control"] == "true"
        assert result["business_tool_access_token"] == "busi****3456"
        assert result["business_tool_read_token"] == "read****3456"
        assert result["business_tool_execute_token"] == "exec****3456"
        assert result["enable_business_tool_audit_file"] == "true"
        assert result["business_tool_audit_file"] == "logs/business_tool_audit.jsonl"
        assert result["risk_api_base_url"] == "https://risk.example.test"
        assert result["profit_api_base_url"] == "https://profit.example.test"


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

    def test_update_business_tool_intent_fields(self, temp_env):
        result = update_llm_settings({
            "enable_business_tools": True,
            "business_tool_timeout": 8,
            "risk_api_base_url": "https://risk.example.test",
            "risk_api_key": "risk-secret",
            "profit_api_base_url": "https://profit.example.test",
            "profit_api_key": "profit-secret",
            "enable_business_tool_llm_intent": True,
            "business_tool_llm_intent_min_confidence": "0.82",
            "enable_business_tool_access_control": True,
            "business_tool_access_token": "business-access-secret",
            "business_tool_read_token": "business-read-secret",
            "business_tool_execute_token": "business-execute-secret",
            "enable_business_tool_audit_file": True,
            "business_tool_audit_file": "logs/business_tool_audit.jsonl",
        })

        assert result["success"] is True
        assert result["updated"] == [
            "enable_business_tools",
            "business_tool_timeout",
            "risk_api_base_url",
            "risk_api_key",
            "profit_api_base_url",
            "profit_api_key",
            "enable_business_tool_llm_intent",
            "business_tool_llm_intent_min_confidence",
            "enable_business_tool_access_control",
            "business_tool_access_token",
            "business_tool_read_token",
            "business_tool_execute_token",
            "enable_business_tool_audit_file",
            "business_tool_audit_file",
        ]

        settings = get_llm_settings()
        assert settings["enable_business_tools"] == "true"
        assert settings["business_tool_timeout"] == "8"
        assert settings["risk_api_base_url"] == "https://risk.example.test"
        assert settings["risk_api_key"] == "risk****cret"
        assert settings["profit_api_base_url"] == "https://profit.example.test"
        assert settings["profit_api_key"] == "prof****cret"
        assert settings["enable_business_tool_llm_intent"] == "true"
        assert settings["business_tool_llm_intent_min_confidence"] == "0.82"
        assert settings["enable_business_tool_access_control"] == "true"
        assert settings["business_tool_access_token"] == "busi****cret"
        assert settings["business_tool_read_token"] == "busi****cret"
        assert settings["business_tool_execute_token"] == "busi****cret"

    def test_update_business_tool_settings_apply_runtime_and_reset_services(
        self,
        temp_env,
        monkeypatch,
    ):
        from api.config import settings

        reset_calls = []
        monkeypatch.setattr(settings, "enable_business_tools", False)
        monkeypatch.setattr(settings, "business_tool_timeout", 5)
        monkeypatch.setattr(settings, "risk_api_base_url", "")
        monkeypatch.setattr(settings, "profit_api_base_url", "")
        monkeypatch.setattr(settings, "enable_business_tool_access_control", False)
        monkeypatch.setattr(settings, "business_tool_access_token", "")
        monkeypatch.setattr(settings, "business_tool_read_token", "")
        monkeypatch.setattr(settings, "business_tool_execute_token", "")
        monkeypatch.setattr(
            "api.services.business_clients.reset_business_clients",
            lambda: reset_calls.append("business_clients"),
        )
        monkeypatch.setattr(
            "api.services.tool_service.reset_tool_service",
            lambda: reset_calls.append("tool_service"),
        )
        monkeypatch.setitem(
            sys.modules,
            "api.services.conversation_agent",
            SimpleNamespace(
                reset_conversation_agent=lambda: reset_calls.append("conversation_agent")
            ),
        )

        result = update_llm_settings({
            "enable_business_tools": True,
            "business_tool_timeout": 9,
            "risk_api_base_url": "https://risk.example.test",
            "profit_api_base_url": "https://profit.example.test",
            "enable_business_tool_access_control": True,
            "business_tool_access_token": "business-access-secret",
            "business_tool_read_token": "business-read-secret",
            "business_tool_execute_token": "business-execute-secret",
        })

        assert result["success"] is True
        assert settings.enable_business_tools is True
        assert settings.business_tool_timeout == 9
        assert settings.risk_api_base_url == "https://risk.example.test"
        assert settings.profit_api_base_url == "https://profit.example.test"
        assert settings.enable_business_tool_access_control is True
        assert settings.business_tool_access_token == "business-access-secret"
        assert settings.business_tool_read_token == "business-read-secret"
        assert settings.business_tool_execute_token == "business-execute-secret"
        assert reset_calls == ["business_clients", "tool_service", "conversation_agent"]
