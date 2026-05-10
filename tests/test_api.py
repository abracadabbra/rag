"""
API 健康检查测试
"""

import sys
from types import ModuleType

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def install_fake_conversation_agent(
    monkeypatch,
    *,
    result=None,
    error=None,
    calls=None,
):
    """安装假的对话 Agent，隔离真实 RAG 依赖。"""

    class FakeAgent:
        def process(self, **kwargs):
            if calls is not None:
                calls.append(kwargs)
            if error is not None:
                raise error
            return result

    fake_module = ModuleType("api.services.conversation_agent")
    fake_module.get_conversation_agent = lambda: FakeAgent()
    monkeypatch.setitem(sys.modules, "api.services.conversation_agent", fake_module)


def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["status"] == "running"


def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"healthy", "degraded"}
    assert "timestamp" in data
    assert "version" in data
    assert "checks" in data
    assert "api" in data["checks"]
    assert "milvus" in data["checks"]
    assert "redis" in data["checks"]


def test_milvus_health():
    """测试 Milvus 健康检查"""
    response = client.get("/health/milvus")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # 注意：如果 Milvus 未启动，status 会是 unhealthy


def test_redis_health():
    """测试 Redis 健康检查"""
    response = client.get("/health/redis")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # 注意：如果 Redis 未启动，status 会是 unhealthy


def test_risk_rules_query_success(monkeypatch):
    """测试查询成功响应和参数透传。"""
    calls = []
    install_fake_conversation_agent(
        monkeypatch,
        calls=calls,
        result={
            "answer": "白金卡单笔交易限额是 50,000 元。",
            "sources": [
                {
                    "score": 0.95,
                    "content_preview": "白金卡单笔限额：50,000 元...",
                    "rule_id": "R001",
                    "rule_name": "信用卡交易限额规则",
                }
            ],
            "retrieved_count": 1,
            "session_id": "session-123",
        },
    )

    response = client.post(
        "/api/v1/risk-rules/query",
        json={
            "query": "白金卡的单笔交易限额是多少？",
            "session_id": "session-123",
            "top_k": 3,
            "score_threshold": 0.6,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "白金卡单笔交易限额是 50,000 元。"
    assert data["retrieved_count"] == 1
    assert data["session_id"] == "session-123"
    assert data["needs_clarification"] is False
    assert len(data["sources"]) == 1

    assert calls == [
        {
            "query": "白金卡的单笔交易限额是多少？",
            "session_id": "session-123",
            "scene_type": "risk_rule",
            "top_k": 3,
            "score_threshold": 0.6,
            "clarification_choice": None,
        }
    ]


def test_risk_rules_query_clarification_response(monkeypatch):
    """测试澄清响应结构。"""
    install_fake_conversation_agent(
        monkeypatch,
        result={
            "answer": "请问您想查询以下哪个方面的信息？",
            "sources": [],
            "retrieved_count": 0,
            "session_id": "session-clarify",
            "needs_clarification": True,
            "clarification_options": ["白金卡单笔限额", "白金卡日累计限额"],
        },
    )

    response = client.post(
        "/api/v1/risk-rules/query",
        json={
            "query": "限额是多少？",
            "clarification_choice": "白金卡单笔限额",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["needs_clarification"] is True
    assert data["clarification_options"] == ["白金卡单笔限额", "白金卡日累计限额"]
    assert data["session_id"] == "session-clarify"


@pytest.mark.parametrize(
    ("error", "status_code", "detail_prefix"),
    [
        (ConnectionError("Milvus unavailable"), 503, "服务暂时不可用"),
        (TimeoutError("LLM timeout"), 504, "请求超时"),
        (ValueError("bad input"), 400, "请求参数错误"),
        (Exception("unexpected"), 500, "查询失败"),
    ],
)
def test_risk_rules_query_error_mapping(monkeypatch, error, status_code, detail_prefix):
    """测试异常到 HTTP 状态码的映射。"""
    install_fake_conversation_agent(monkeypatch, error=error)

    response = client.post(
        "/api/v1/risk-rules/query",
        json={"query": "测试查询"},
    )

    assert response.status_code == status_code
    assert response.json()["detail"].startswith(detail_prefix)
