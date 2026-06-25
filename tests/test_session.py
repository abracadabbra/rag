"""
会话管理器测试
"""

import time

import pytest
from fastapi.testclient import TestClient

import api.services.session_manager as session_manager_module
from api.main import app
from api.services.session_manager import SessionManager, get_session_manager
from tests.fakes import FakeRedis


client = TestClient(app)


@pytest.fixture
def session_manager():
    """创建会话管理器实例"""
    return SessionManager(redis_client=FakeRedis())


def test_create_session(session_manager):
    """测试创建会话"""
    # 自动生成 session_id
    session_id = session_manager.create_session()
    assert session_id is not None
    assert len(session_id) == 36  # UUID 格式

    # 指定 session_id
    custom_id = "test-session-123"
    session_id = session_manager.create_session(custom_id)
    assert session_id == custom_id


def test_get_session(session_manager):
    """测试获取会话"""
    # 创建会话
    session_id = session_manager.create_session()

    # 获取会话
    state = session_manager.get_session(session_id)
    assert state is not None
    assert state.session_id == session_id
    assert len(state.messages) == 0

    # 获取不存在的会话
    state = session_manager.get_session("non-existent")
    assert state is None


def test_add_message(session_manager):
    """测试添加消息"""
    session_id = session_manager.create_session()

    # 添加用户消息
    success = session_manager.add_message(
        session_id=session_id,
        role="user",
        content="白金卡的单笔限额是多少？"
    )
    assert success is True

    # 添加助手消息
    success = session_manager.add_message(
        session_id=session_id,
        role="assistant",
        content="白金卡的单笔交易限额是 50,000 元。"
    )
    assert success is True

    # 验证消息
    state = session_manager.get_session(session_id)
    assert len(state.messages) == 2
    assert state.messages[0].role == "user"
    assert state.messages[1].role == "assistant"


def test_add_message_stores_message_level_metadata(session_manager):
    """测试消息级元数据不会被会话级最新元数据污染"""
    session_id = session_manager.create_session()

    session_manager.add_message(
        session_id=session_id,
        role="assistant",
        content="第一次回答",
        metadata={
            "tool_calls": [{"name": "get_risk_event_detail"}],
            "tool_intent": {"tool_name": "get_risk_event_detail"},
        },
    )
    session_manager.add_message(
        session_id=session_id,
        role="assistant",
        content="第二次回答",
        metadata={
            "tool_calls": [{"name": "get_profit_chain_detail"}],
            "tool_intent": {"tool_name": "get_profit_chain_detail"},
        },
    )

    state = session_manager.get_session(session_id)

    assert state.metadata["tool_intent"]["tool_name"] == "get_profit_chain_detail"
    assert state.messages[0].metadata["tool_calls"][0]["name"] == "get_risk_event_detail"
    assert state.messages[0].metadata["tool_intent"]["tool_name"] == "get_risk_event_detail"
    assert state.messages[1].metadata["tool_calls"][0]["name"] == "get_profit_chain_detail"
    assert state.messages[1].metadata["tool_intent"]["tool_name"] == "get_profit_chain_detail"


def test_conversation_history(session_manager):
    """测试对话历史"""
    session_id = session_manager.create_session()

    # 添加多条消息
    messages = [
        ("user", "问题1"),
        ("assistant", "答案1"),
        ("user", "问题2"),
        ("assistant", "答案2"),
        ("user", "问题3"),
    ]

    for role, content in messages:
        session_manager.add_message(session_id, role, content)

    # 获取全部历史
    history = session_manager.get_conversation_history(session_id)
    assert len(history) == 5

    # 获取最近 3 条
    history = session_manager.get_conversation_history(session_id, limit=3)
    assert len(history) == 3
    assert history[0].content == "问题2"
    assert history[1].content == "答案2"
    assert history[2].content == "问题3"


def test_update_metadata(session_manager):
    """测试更新元数据"""
    session_id = session_manager.create_session()

    # 更新元数据
    metadata = {
        "user_id": "user123",
        "scene_type": "risk_rule"
    }
    success = session_manager.update_metadata(session_id, metadata)
    assert success is True

    # 验证元数据
    state = session_manager.get_session(session_id)
    assert state.metadata["user_id"] == "user123"
    assert state.metadata["scene_type"] == "risk_rule"

    # 追加元数据
    session_manager.update_metadata(session_id, {"extra": "value"})
    state = session_manager.get_session(session_id)
    assert state.metadata["extra"] == "value"
    assert state.metadata["user_id"] == "user123"  # 原有数据保留


def test_get_session_endpoint_returns_message_level_metadata(monkeypatch):
    """测试会话详情接口返回每条消息自己的元数据"""
    manager = SessionManager(redis_client=FakeRedis())
    session_id = manager.create_session("metadata-session")
    manager.add_message(
        session_id=session_id,
        role="assistant",
        content="风控回答",
        metadata={"tool_calls": [{"name": "get_risk_event_detail"}]},
    )
    manager.add_message(
        session_id=session_id,
        role="assistant",
        content="毛利回答",
        metadata={"tool_calls": [{"name": "get_profit_chain_detail"}]},
    )
    monkeypatch.setattr("api.routers.sessions.get_session_manager", lambda: manager)

    response = client.get(f"/api/v1/sessions/{session_id}")

    assert response.status_code == 200
    messages = response.json()["messages"]
    assert messages[0]["metadata"]["tool_calls"][0]["name"] == "get_risk_event_detail"
    assert messages[1]["metadata"]["tool_calls"][0]["name"] == "get_profit_chain_detail"


def test_delete_session(session_manager):
    """测试删除会话"""
    session_id = session_manager.create_session()

    # 删除会话
    success = session_manager.delete_session(session_id)
    assert success is True

    # 验证已删除
    state = session_manager.get_session(session_id)
    assert state is None

    # 删除不存在的会话
    success = session_manager.delete_session("non-existent")
    assert success is False


def test_session_ttl(session_manager):
    """测试会话过期"""
    # 创建短 TTL 的会话管理器
    session_manager.ttl = 2  # 2 秒过期

    session_id = session_manager.create_session()
    session_manager.add_message(session_id, "user", "测试消息")

    # 立即获取，应该存在
    state = session_manager.get_session(session_id)
    assert state is not None

    # 等待过期
    time.sleep(3)

    # 再次获取，应该已过期
    state = session_manager.get_session(session_id)
    assert state is None


def test_extend_ttl(session_manager):
    """测试延长 TTL"""
    session_manager.ttl = 2  # 2 秒过期

    session_id = session_manager.create_session()

    # 等待 1 秒
    time.sleep(1)

    # 延长 TTL
    success = session_manager.extend_ttl(session_id)
    assert success is True

    # 再等待 1.5 秒（如果没有延长，此时应该已过期）
    time.sleep(1.5)

    # 应该仍然存在
    state = session_manager.get_session(session_id)
    assert state is not None


def test_get_session_manager_singleton(monkeypatch):
    """测试单例模式"""
    fake_redis = FakeRedis()
    monkeypatch.setattr(session_manager_module, "_session_manager", None)
    monkeypatch.setattr(session_manager_module, "_redis_client", fake_redis)

    manager1 = get_session_manager()
    manager2 = get_session_manager()

    assert manager1 is manager2
    assert manager1.redis_client is fake_redis


def test_concurrent_sessions(session_manager):
    """测试并发会话"""
    # 创建多个会话
    session_ids = [
        session_manager.create_session()
        for _ in range(5)
    ]

    # 每个会话添加不同的消息
    for i, session_id in enumerate(session_ids):
        session_manager.add_message(
            session_id,
            "user",
            f"问题 {i}"
        )

    # 验证每个会话独立
    for i, session_id in enumerate(session_ids):
        state = session_manager.get_session(session_id)
        assert len(state.messages) == 1
        assert state.messages[0].content == f"问题 {i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
