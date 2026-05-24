"""
Settings API 端点集成测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_settings_service(tmp_path):
    """隔离 settings 服务，使用临时 .env 文件"""
    env_file = tmp_path / ".env"
    with patch("api.services.settings_service.ENV_FILE", env_file):
        yield env_file


class TestGetSettings:
    """GET /api/v1/settings/ 测试"""

    def test_returns_all_keys(self):
        response = client.get("/api/v1/settings/")
        assert response.status_code == 200
        data = response.json()
        assert "llm_provider" in data
        assert "minimax_api_key" in data
        assert "openai_api_key" in data

    def test_api_keys_masked(self):
        response = client.get("/api/v1/settings/")
        data = response.json()
        # 默认为空，不是 mask 格式
        assert data["minimax_api_key"] == ""


class TestPatchSettings:
    """PATCH /api/v1/settings/ 测试"""

    def test_update_provider(self):
        response = client.patch(
            "/api/v1/settings/",
            json={"llm_provider": "openai"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "llm_provider" in data["updated"]

    def test_empty_body_rejected(self):
        response = client.patch("/api/v1/settings/", json={})
        assert response.status_code == 400
        assert "未提供" in response.json()["detail"]

    def test_invalid_provider_rejected(self):
        response = client.patch(
            "/api/v1/settings/",
            json={"llm_provider": "invalid"},
        )
        assert response.status_code == 422
        assert "无效" in response.json()["detail"]

    def test_valid_providers_accepted(self):
        for provider in ("minimax", "openai", "local"):
            response = client.patch(
                "/api/v1/settings/",
                json={"llm_provider": provider},
            )
            assert response.status_code == 200

    def test_temperature_validation(self):
        response = client.patch(
            "/api/v1/settings/",
            json={"openai_temperature": 3.0},
        )
        assert response.status_code == 422

    def test_temperature_valid(self):
        response = client.patch(
            "/api/v1/settings/",
            json={"openai_temperature": 1.5},
        )
        assert response.status_code == 200

    def test_max_tokens_validation(self):
        response = client.patch(
            "/api/v1/settings/",
            json={"openai_max_tokens": 0},
        )
        assert response.status_code == 422

    def test_max_tokens_valid(self):
        response = client.patch(
            "/api/v1/settings/",
            json={"openai_max_tokens": 4096},
        )
        assert response.status_code == 200

    def test_update_multiple_fields(self):
        response = client.patch(
            "/api/v1/settings/",
            json={
                "llm_provider": "minimax",
                "minimax_model": "test-model",
                "minimax_api_base": "https://api.test.com",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["updated"]) == 3
