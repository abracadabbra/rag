"""
澄清服务单元测试
"""

import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest


def load_clarification_module(monkeypatch, *, content="CLEAR", error=None):
    """在无真实 openai 依赖下加载 clarification 模块。"""

    class FakeOpenAI:
        def __init__(self, *args, **kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=self._create)
            )

        def _create(self, **kwargs):
            if error is not None:
                raise error
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=content)
                    )
                ]
            )

    fake_openai_module = ModuleType("openai")
    fake_openai_module.OpenAI = FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", fake_openai_module)
    monkeypatch.delitem(sys.modules, "api.services.clarification", raising=False)

    return importlib.import_module("api.services.clarification")


def create_service(monkeypatch, *, content="CLEAR", error=None):
    module = load_clarification_module(monkeypatch, content=content, error=error)
    return module.ClarificationService()


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("呢", True),
        ("多少？", True),
        ("限额呢？", True),
        ("白金卡单笔交易限额是多少？", False),
    ],
)
def test_is_too_vague(monkeypatch, query, expected):
    service = create_service(monkeypatch)

    assert service._is_too_vague(query) is expected


def test_has_multiple_categories_and_extract(monkeypatch):
    service = create_service(monkeypatch)
    docs = [
        {"metadata": {"category": "白金卡"}},
        {"metadata": {"product": "金卡"}},
        {"metadata": {"category": "白金卡"}},
    ]

    assert service._has_multiple_categories(docs) is True
    assert service._extract_categories(docs) == ["白金卡", "金卡"]


def test_generate_clarification_options_parses_and_limits_results(monkeypatch):
    service = create_service(
        monkeypatch,
        content="CLARIFY:\n1. 白金卡单笔限额\n2. 白金卡日累计限额\n3. 金卡单笔限额\n4. 普卡限额",
    )

    options = service._generate_clarification_options(
        query="限额是多少？",
        conversation_history=[{"role": "user", "content": "帮我查卡片限额"}],
        retrieved_docs=[{"metadata": {"rule_name": "信用卡交易限额规则"}}],
    )

    assert options == ["白金卡单笔限额", "白金卡日累计限额", "金卡单笔限额"]


def test_generate_clarification_options_returns_empty_on_error(monkeypatch):
    service = create_service(monkeypatch, error=RuntimeError("llm failed"))

    options = service._generate_clarification_options(
        query="限额是多少？",
        conversation_history=[],
        retrieved_docs=[],
    )

    assert options == []


def test_needs_clarification_for_vague_query(monkeypatch):
    service = create_service(
        monkeypatch,
        content="CLARIFY:\n1. 白金卡单笔限额\n2. 白金卡日累计限额",
    )

    needs_clarification, options = service.needs_clarification(
        query="限额呢？",
        conversation_history=[{"role": "user", "content": "查一下白金卡"}],
        retrieved_docs=[{"metadata": {"rule_name": "信用卡交易限额规则"}}],
    )

    assert needs_clarification is True
    assert options == ["白金卡单笔限额", "白金卡日累计限额"]


def test_needs_clarification_for_multiple_categories(monkeypatch):
    service = create_service(monkeypatch, content="CLEAR")

    needs_clarification, options = service.needs_clarification(
        query="白金卡和金卡限额对比",
        conversation_history=[],
        retrieved_docs=[
            {"metadata": {"category": "白金卡"}},
            {"metadata": {"category": "金卡"}},
        ],
    )

    assert needs_clarification is True
    assert options == ["白金卡", "金卡"]


def test_needs_clarification_returns_false_when_query_is_clear(monkeypatch):
    service = create_service(monkeypatch, content="CLEAR")

    needs_clarification, options = service.needs_clarification(
        query="白金卡单笔交易限额是多少？",
        conversation_history=[],
        retrieved_docs=[{"metadata": {"category": "白金卡"}}],
    )

    assert needs_clarification is False
    assert options == []
