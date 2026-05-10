"""
RAG 服务单元测试
"""

import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest


class FakeCacheService:
    def __init__(self, cached_result=None):
        self.cached_result = cached_result
        self.get_calls = []
        self.set_calls = []

    def get(self, **kwargs):
        self.get_calls.append(kwargs)
        return self.cached_result

    def set(self, **kwargs):
        self.set_calls.append(kwargs)
        return True


class FakeEntity:
    def __init__(self, data):
        self.data = data

    def get(self, key, default=None):
        return self.data.get(key, default)


def make_hit(score, content, metadata=None, scene_type="risk_rule"):
    return SimpleNamespace(
        score=score,
        entity=FakeEntity(
            {
                "content": content,
                "metadata": metadata or {},
                "scene_type": scene_type,
            }
        ),
    )


def load_rag_module(
    monkeypatch,
    *,
    search_results=None,
    search_error=None,
    llm_content="默认答案",
    llm_error=None,
    cache_service=None,
    embed_vector=None,
):
    """在无真实 pymilvus/openai 依赖下加载 rag_service 模块。"""

    tracker = SimpleNamespace(
        connect_calls=[],
        embed_calls=[],
        llm_calls=[],
        collection=None,
    )
    cache_service = cache_service or FakeCacheService()
    embed_vector = embed_vector or [0.1, 0.2, 0.3]

    class FakeCollection:
        def __init__(self, name):
            self.name = name
            self.search_calls = []
            self.loaded = False
            tracker.collection = self

        def load(self):
            self.loaded = True

        def search(self, **kwargs):
            self.search_calls.append(kwargs)
            if search_error is not None:
                raise search_error
            return [search_results or []]

    def fake_connect(**kwargs):
        tracker.connect_calls.append(kwargs)

    class FakeOpenAI:
        def __init__(self, *args, **kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=self._create)
            )

        def _create(self, **kwargs):
            tracker.llm_calls.append(kwargs)
            if llm_error is not None:
                raise llm_error
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=llm_content))],
                usage=SimpleNamespace(
                    prompt_tokens=12,
                    completion_tokens=7,
                    total_tokens=19,
                ),
            )

    fake_pymilvus_module = ModuleType("pymilvus")
    fake_pymilvus_module.connections = SimpleNamespace(connect=fake_connect)
    fake_pymilvus_module.Collection = FakeCollection

    fake_openai_module = ModuleType("openai")
    fake_openai_module.OpenAI = FakeOpenAI

    fake_embeddings_module = ModuleType("ingestion.embeddings")

    def fake_embed_query(query):
        tracker.embed_calls.append(query)
        return embed_vector

    fake_embeddings_module.embed_query = fake_embed_query

    fake_cache_module = ModuleType("api.services.cache_service")
    fake_cache_module.get_cache_service = lambda: cache_service

    monkeypatch.setitem(sys.modules, "pymilvus", fake_pymilvus_module)
    monkeypatch.setitem(sys.modules, "openai", fake_openai_module)
    monkeypatch.setitem(sys.modules, "ingestion.embeddings", fake_embeddings_module)
    monkeypatch.setitem(sys.modules, "api.services.cache_service", fake_cache_module)
    monkeypatch.delitem(sys.modules, "api.services.rag_service", raising=False)

    module = importlib.import_module("api.services.rag_service")
    return module, tracker, cache_service


def test_query_returns_cached_result_without_embedding_or_search(monkeypatch):
    cached_result = {
        "answer": "缓存答案",
        "sources": [{"score": 0.99}],
        "retrieved_count": 1,
    }
    module, tracker, cache_service = load_rag_module(
        monkeypatch,
        cache_service=FakeCacheService(cached_result=cached_result),
    )
    service = module.RAGService()

    result = service.query(query="白金卡限额", scene_type="risk_rule")

    assert result == cached_result
    assert cache_service.get_calls[0]["query"] == "白金卡限额"
    assert tracker.embed_calls == []
    assert tracker.collection.search_calls == []
    assert tracker.llm_calls == []
    assert cache_service.set_calls == []


def test_query_filters_hits_generates_answer_and_writes_cache(monkeypatch):
    module, tracker, cache_service = load_rag_module(
        monkeypatch,
        search_results=[
            make_hit(
                0.95,
                "白金卡单笔限额 50,000 元",
                {
                    "rule_id": "R001",
                    "rule_name": "信用卡交易限额规则",
                    "source": "risk_rules/R001.md",
                    "chunk_index": 2,
                },
            ),
            make_hit(0.4, "低分内容", {"rule_id": "R999"}),
        ],
        llm_content="白金卡单笔交易限额是 50,000 元。【文档 1】",
    )
    service = module.RAGService()

    result = service.query(
        query="白金卡的单笔交易限额是多少？",
        scene_type="risk_rule",
        top_k=3,
        score_threshold=0.7,
    )

    assert result["answer"] == "白金卡单笔交易限额是 50,000 元。【文档 1】"
    assert result["retrieved_count"] == 1
    assert result["sources"] == [
        {
            "score": 0.95,
            "content_preview": "白金卡单笔限额 50,000 元...",
            "rule_id": "R001",
            "rule_name": "信用卡交易限额规则",
            "file_path": "risk_rules/R001.md",
            "chunk_index": 2,
        }
    ]
    assert tracker.embed_calls == ["白金卡的单笔交易限额是多少？"]
    assert tracker.collection.loaded is True
    assert tracker.collection.search_calls[0]["expr"] == 'scene_type == "risk_rule"'
    assert tracker.collection.search_calls[0]["limit"] == 3
    assert tracker.llm_calls[0]["model"]
    assert "白金卡单笔限额 50,000 元" in tracker.llm_calls[0]["messages"][1]["content"]
    assert cache_service.set_calls[0]["result"] == result


def test_query_returns_empty_result_when_no_doc_matches_threshold(monkeypatch):
    module, tracker, cache_service = load_rag_module(
        monkeypatch,
        search_results=[make_hit(0.6, "命中但低于阈值", {"rule_id": "R001"})],
    )
    service = module.RAGService()

    result = service.query(
        query="未知问题",
        scene_type="risk_rule",
        score_threshold=0.7,
    )

    assert result == {
        "answer": "抱歉，我没有找到相关的信息。请尝试换一种方式提问。",
        "sources": [],
        "retrieved_count": 0,
    }
    assert tracker.embed_calls == ["未知问题"]
    assert tracker.llm_calls == []
    assert cache_service.set_calls == []


def test_query_maps_search_error_to_connection_error(monkeypatch):
    module, _tracker, _cache_service = load_rag_module(
        monkeypatch,
        search_error=RuntimeError("milvus down"),
    )
    service = module.RAGService()

    with pytest.raises(ConnectionError, match="向量检索失败"):
        service.query(query="测试", scene_type="risk_rule")


def test_build_context_prompt_and_format_sources(monkeypatch):
    module, _tracker, _cache_service = load_rag_module(monkeypatch)
    service = module.RAGService()
    docs = [
        {
            "content": "白金卡单笔限额 50,000 元",
            "metadata": {
                "rule_id": "R001",
                "rule_name": "信用卡交易限额规则",
                "source": "risk_rules/R001.md",
                "chunk_index": 1,
            },
            "score": 0.95234,
        }
    ]

    context = service._build_context(docs)
    prompt = service._build_prompt("白金卡限额是多少？", context, "risk_rule")
    sources = service._format_sources(docs)

    assert "【文档 1】 规则ID: R001 | 信用卡交易限额规则" in context
    assert "你是一个专业的风控规则问答助手" in prompt
    assert "白金卡限额是多少？" in prompt
    assert sources == [
        {
            "score": 0.9523,
            "content_preview": "白金卡单笔限额 50,000 元...",
            "rule_id": "R001",
            "rule_name": "信用卡交易限额规则",
            "file_path": "risk_rules/R001.md",
            "chunk_index": 1,
        }
    ]


@pytest.mark.parametrize(
    ("llm_error", "expected_exception", "expected_message"),
    [
        (TimeoutError("slow"), TimeoutError, "LLM 响应超时"),
        (Exception("authentication failed"), ConnectionError, "OpenAI API 认证失败"),
        (Exception("boom"), ConnectionError, "LLM 调用失败"),
    ],
)
def test_generate_answer_maps_llm_errors(monkeypatch, llm_error, expected_exception, expected_message):
    module, _tracker, _cache_service = load_rag_module(
        monkeypatch,
        llm_error=llm_error,
    )
    service = module.RAGService()

    with pytest.raises(expected_exception, match=expected_message):
        service._generate_answer("测试 prompt")
