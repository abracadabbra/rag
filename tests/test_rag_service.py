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
    hit_id = metadata.get("rule_id") if isinstance(metadata, dict) else None
    return {
        "distance": score,
        "id": hit_id,
        "entity": {
            "content": content,
            "metadata": metadata or {},
            "scene_type": scene_type,
        },
    }


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

        def query(self, **kwargs):
            self.search_calls.append(kwargs)
            scene_filter = kwargs.get("filter", "")
            if 'scene_type == "profit"' in scene_filter:
                return [{"id": "profit_1", "scene_type": "profit"}]
            return []

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
            if kwargs.get("stream"):
                return [
                    SimpleNamespace(
                        choices=[
                            SimpleNamespace(
                                delta=SimpleNamespace(content=llm_content)
                            )
                        ]
                    ),
                    SimpleNamespace(choices=[]),
                ]
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

    class FakeEmbeddingGenerator:
        def embed_query(self, query):
            return embed_vector

    def fake_get_embedding_generator():
        return FakeEmbeddingGenerator()

    fake_embeddings_module.embed_query = fake_embed_query
    fake_embeddings_module.get_embedding_generator = fake_get_embedding_generator

    fake_ingestion_module = ModuleType("ingestion")
    fake_ingestion_module.embeddings = fake_embeddings_module

    fake_milvus_client_module = ModuleType("ingestion.milvus_client")
    fake_milvus_client_module.get_milvus_client = lambda **kwargs: FakeCollection(
        kwargs["collection_name"]
    )

    fake_cache_module = ModuleType("api.services.cache_service")
    fake_cache_module.get_cache_service = lambda: cache_service

    class FakeBM25Indexer:
        def search(self, **kwargs):
            return []

    fake_bm25_module = ModuleType("api.services.bm25_service")
    fake_bm25_module.get_bm25_indexer = lambda: FakeBM25Indexer()
    fake_bm25_module.compute_bm25_scores_dynamic = lambda *args, **kwargs: []

    class FakeReranker:
        def rerank(self, query, documents, top_k=None):
            return documents[:top_k] if top_k else documents

    fake_rerank_module = ModuleType("api.services.rerank_service")
    fake_rerank_module.get_reranker = lambda: FakeReranker()

    fake_hybrid_module = ModuleType("api.services.hybrid_search")
    fake_hybrid_module.reciprocal_rank_fusion = lambda result_lists, k=60: [
        doc for result_list in result_lists for doc in result_list
    ]
    fake_hybrid_module.hybrid_search = lambda vector_results, bm25_results, **kwargs: (
        vector_results + bm25_results
    )

    monkeypatch.setitem(sys.modules, "pymilvus", fake_pymilvus_module)
    monkeypatch.setitem(sys.modules, "openai", fake_openai_module)
    monkeypatch.setitem(sys.modules, "ingestion", fake_ingestion_module)
    monkeypatch.setitem(sys.modules, "ingestion.embeddings", fake_embeddings_module)
    monkeypatch.setitem(sys.modules, "ingestion.milvus_client", fake_milvus_client_module)
    monkeypatch.setitem(sys.modules, "api.services.cache_service", fake_cache_module)
    monkeypatch.setitem(sys.modules, "api.services.bm25_service", fake_bm25_module)
    monkeypatch.setitem(sys.modules, "api.services.rerank_service", fake_rerank_module)
    monkeypatch.setitem(sys.modules, "api.services.hybrid_search", fake_hybrid_module)
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
            make_hit(0.4, "低分内容", {"rule_id": "R999"}, scene_type="model_card"),
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
            "source_type": "vector",
            "scene_type": "risk_rule",
            "rule_id": "R001",
            "rule_name": "信用卡交易限额规则",
            "file_path": "risk_rules/R001.md",
            "chunk_index": 2,
        }
    ]
    assert tracker.embed_calls == ["白金卡的单笔交易限额是多少？"]
    assert tracker.collection.search_calls[0]["collection_name"]
    assert tracker.collection.search_calls[0]["limit"] == 6
    assert tracker.llm_calls[0]["model"]
    assert "白金卡单笔限额 50,000 元" in tracker.llm_calls[0]["messages"][1]["content"]
    assert cache_service.set_calls[0]["result"] == result


def test_query_returns_empty_result_when_no_doc_matches_scene(monkeypatch):
    module, tracker, cache_service = load_rag_module(
        monkeypatch,
        search_results=[
            make_hit(0.6, "其他场景内容", {"rule_id": "R001"}, scene_type="model_card")
        ],
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
        "retrieval_metadata": {
            "vector_count": 0,
            "bm25_count": 0,
            "final_count": 0,
            "used_rerank": False,
            "used_bm25": False,
        },
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
                "scene_type": "risk_rule",
                "score": 0.95234,
            }
        ]

    context = service._build_context(docs)
    prompt = service._build_prompt("白金卡限额是多少？", context, "risk_rule")
    sources = service._format_sources(docs)

    assert "【文档 1】 规则ID: R001 | 信用卡交易限额规则" in context
    assert "你是一个专业的风控规则问答助手" in prompt
    assert "风控结论" in prompt
    assert "命中规则/依据" in prompt
    assert "处置建议" in prompt
    assert "风控策略视角" in prompt
    assert "规则阈值" in prompt
    assert "白金卡限额是多少？" in prompt
    assert sources == [
        {
            "score": 0.9523,
            "content_preview": "白金卡单笔限额 50,000 元...",
            "source_type": "vector",
            "scene_type": "risk_rule",
            "rule_id": "R001",
            "rule_name": "信用卡交易限额规则",
            "file_path": "risk_rules/R001.md",
            "chunk_index": 1,
        }
    ]


def test_query_stream_normalizes_string_metadata(monkeypatch):
    module, tracker, _cache_service = load_rag_module(
        monkeypatch,
        search_results=[
            make_hit(
                0.88,
                "平台抽成 15%，司机收入按结算规则计算",
                (
                    '{"rule_id":"P001","rule_name":"毛利结算规则",'
                    '"source":"profit/P001.md","chunk_index":3}'
                ),
                scene_type="profit",
            )
        ],
        llm_content="流式毛利答案",
    )
    service = module.RAGService()

    events = list(
        service.query_stream(
            query="查询订单 ORD88888 的抽成和司机收入",
            scene_type="profit",
            top_k=1,
            tool_context="订单 ORD88888 平台净毛利 2.33 元。",
        )
    )

    assert events[0]["type"] == "sources"
    assert events[0]["data"]["retrieved_count"] == 1
    assert events[0]["data"]["sources"][0]["scene_type"] == "profit"
    assert events[0]["data"]["sources"][0]["rule_id"] == "P001"
    assert events[0]["data"]["sources"][0]["rule_name"] == "毛利结算规则"
    assert events[0]["data"]["sources"][0]["file_path"] == "profit/P001.md"
    assert events[0]["data"]["sources"][0]["chunk_index"] == 3
    assert events[1] == {"type": "chunk", "data": "流式毛利答案"}
    assert events[2] == {"type": "done", "data": ""}
    assert tracker.llm_calls[0]["stream"] is True
    assert "规则ID: P001 | 毛利结算规则" in tracker.llm_calls[0]["messages"][1]["content"]


def test_query_stream_filters_sources_by_scene(monkeypatch):
    module, tracker, _cache_service = load_rag_module(
        monkeypatch,
        search_results=[
            make_hit(
                0.92,
                "毛利链路口径文档",
                {"rule_id": "P001", "rule_name": "订单毛利链路"},
                scene_type="profit",
            ),
            make_hit(
                0.91,
                "模型卡片部署文档",
                {"rule_id": "M001", "rule_name": "模型卡片"},
                scene_type="model_card",
            ),
        ],
        llm_content="流式毛利答案",
    )
    service = module.RAGService()

    events = list(
        service.query_stream(
            query="查询订单 ORD88888 的毛利",
            scene_type="profit",
            top_k=2,
        )
    )

    sources = events[0]["data"]["sources"]
    assert events[0]["data"]["retrieved_count"] == 1
    assert sources == [
        {
            "score": 0.92,
            "content_preview": "毛利链路口径文档...",
            "source_type": "vector",
            "scene_type": "profit",
            "rule_id": "P001",
            "rule_name": "订单毛利链路",
        }
    ]
    assert "毛利链路口径文档" in tracker.llm_calls[0]["messages"][1]["content"]
    assert "模型卡片部署文档" not in tracker.llm_calls[0]["messages"][1]["content"]


def test_corpus_scene_status_returns_safe_scene_availability(monkeypatch):
    module, tracker, _cache_service = load_rag_module(monkeypatch)
    service = module.RAGService()

    status = service.corpus_scene_status(["risk_rule", "profit"])

    assert status == {
        "collection_name": "unified_docs",
        "scenes": {
            "risk_rule": {
                "available": False,
                "sample_count": 0,
                "error_type": None,
            },
            "profit": {
                "available": True,
                "sample_count": 1,
                "error_type": None,
            },
        },
    }
    query_calls = tracker.collection.search_calls
    assert query_calls[0]["filter"] == 'scene_type == "risk_rule"'
    assert query_calls[0]["output_fields"] == ["id", "scene_type"]
    assert query_calls[0]["limit"] == 1
    assert query_calls[1]["filter"] == 'scene_type == "profit"'


def test_query_uses_tool_context_fallback_when_llm_fails(monkeypatch):
    module, _tracker, cache_service = load_rag_module(
        monkeypatch,
        search_results=[],
        llm_error=Exception("network down"),
    )
    service = module.RAGService()

    result = service.query(
        query="查询订单 ORD88888 的抽成和司机收入",
        scene_type="profit",
        tool_context=(
            "订单 ORD88888 平台抽成 19.29 元，司机收入 92.35 元，平台净毛利 2.33 元。\n"
            "链路来源: 自动派生链路\n"
            "毛利公式核对: 平台抽成 - 平台补贴 - 用户优惠 - 渠道费 = 计算净毛利；"
            "计算值 2.33 元，接口净毛利 2.33 元，差异 +0.00 元，状态: 一致"
        ),
    )

    assert result["retrieved_count"] == 0
    assert result["sources"] == []
    assert "业务系统接口数据已返回" in result["answer"]
    assert "当前钱流链路来源：自动派生链路。" in result["answer"]
    assert "毛利公式核对结果：平台抽成 - 平台补贴 - 用户优惠 - 渠道费 = 计算净毛利" in result["answer"]
    assert "计算值 2.33 元，接口净毛利 2.33 元，差异 +0.00 元，状态: 一致" in result["answer"]
    assert "订单 ORD88888 平台抽成 19.29 元" in result["answer"]
    assert cache_service.set_calls == []


def test_query_fallback_surfaces_profit_formula_mismatch(monkeypatch):
    module, _tracker, _cache_service = load_rag_module(
        monkeypatch,
        search_results=[],
        llm_error=Exception("network down"),
    )
    service = module.RAGService()

    result = service.query(
        query="查询订单 ORD88888 的抽成和司机收入",
        scene_type="profit",
        tool_context=(
            "订单 ORD88888 平台抽成 19.29 元，司机收入 92.35 元，平台净毛利 4.00 元。\n"
            "毛利公式核对: 平台抽成 - 平台补贴 - 用户优惠 - 渠道费 = 计算净毛利；"
            "计算值 5.29 元，接口净毛利 4.00 元，差异 +1.29 元，状态: 不一致；未返回渠道费，按 0 核对"
        ),
    )

    assert "毛利公式核对结果：平台抽成 - 平台补贴 - 用户优惠 - 渠道费 = 计算净毛利" in result["answer"]
    assert "状态: 不一致" in result["answer"]
    assert "未返回渠道费，按 0 核对" in result["answer"]


def test_query_fallback_surfaces_api_chain_source_naturally(monkeypatch):
    module, _tracker, _cache_service = load_rag_module(
        monkeypatch,
        search_results=[],
        llm_error=Exception("network down"),
    )
    service = module.RAGService()

    result = service.query(
        query="查询订单 ORD88888 的抽成和司机收入",
        scene_type="profit",
        tool_context=(
            "订单 ORD88888 平台抽成 19.29 元，司机收入 92.35 元，平台净毛利 2.33 元。\n"
            "链路来源: 接口原生链路"
        ),
    )

    assert "当前钱流链路来源：接口原生链路。" in result["answer"]
    assert "链路来源: 接口原生链路" in result["answer"]


def test_query_stream_uses_tool_context_fallback_when_llm_fails(monkeypatch):
    module, _tracker, _cache_service = load_rag_module(
        monkeypatch,
        search_results=[],
        llm_error=Exception("network down"),
    )
    service = module.RAGService()

    events = list(
        service.query_stream(
            query="订单 ORD12345 为什么被风控拦截？",
            scene_type="risk_rule",
            tool_context="订单 ORD12345 风控决策为 block，风险分 87，命中规则: 短时间多次高额交易。",
        )
    )

    assert events[0]["type"] == "sources"
    assert events[0]["data"]["retrieved_count"] == 0
    assert events[1]["type"] == "chunk"
    assert "业务系统接口数据已返回" in events[1]["data"]
    assert "订单 ORD12345 风控决策为 block" in events[1]["data"]
    assert events[2] == {"type": "done", "data": ""}


def test_query_fallback_surfaces_risk_evidence_summary(monkeypatch):
    module, _tracker, _cache_service = load_rag_module(
        monkeypatch,
        search_results=[],
        llm_error=Exception("network down"),
    )
    service = module.RAGService()

    result = service.query(
        query="订单 ORD12345 为什么被风控拦截？",
        scene_type="risk_rule",
        tool_context=(
            "风控证据摘要: 决策=block，风险分=87，风险等级=high，"
            "命中规则数=1，建议动作=建议保持拦截并二次验证，"
            "命中规则=短时间多次高额交易(RISK-velocity-001)\n"
            "订单 ORD12345 风控决策为 block，风险分 87。"
        ),
    )

    assert "业务系统接口数据已返回" in result["answer"]
    assert "风控证据摘要结果：决策=block，风险分=87，风险等级=high" in result["answer"]
    assert "命中规则数=1，建议动作=建议保持拦截并二次验证" in result["answer"]
    assert "短时间多次高额交易(RISK-velocity-001)" in result["answer"]


def test_build_profit_prompt_includes_money_flow_requirements_and_tool_context(monkeypatch):
    module, _tracker, _cache_service = load_rag_module(monkeypatch)
    service = module.RAGService()

    prompt = service._build_prompt(
        query="查询订单 ORD88888 的抽成和司机收入",
        context="【文档 1】平台抽成按订单规则计算",
        scene_type="profit",
        tool_context=(
            "订单 ORD88888 平台抽成 19.29 元，司机收入 92.35 元，平台净毛利 2.33 元。\n"
            "链路来源: 接口原生链路\n"
            "毛利公式核对: 平台抽成 - 平台补贴 - 用户优惠 - 渠道费 = 计算净毛利；"
            "计算值 2.33 元，接口净毛利 2.33 元，差异 +0.00 元，状态: 一致"
        ),
    )

    assert "你是一个专业的毛利抽成问答助手" in prompt
    assert "## 系统接口数据" in prompt
    assert "订单 ORD88888 平台抽成 19.29 元" in prompt
    assert "毛利公式核对" in prompt
    assert "计算值 2.33 元，接口净毛利 2.33 元，差异 +0.00 元，状态: 一致" in prompt
    assert "钱流链路" in prompt
    assert "平台抽成" in prompt
    assert "司机收入" in prompt
    assert "净毛利" in prompt
    assert "## 回答口径" in prompt
    assert "主口径：运营口径" in prompt
    assert "财务口径" in prompt
    assert "运营口径" in prompt
    assert "避免把乘客支付直接当作平台收入" in prompt
    assert "建议输出段落" in prompt
    assert "订单结论：用一句话说明平台净毛利、结算状态和是否异常" in prompt
    assert "为什么调用该接口" in prompt
    assert "如果系统接口数据包含链路来源，明确说明该链路是接口原生返回还是按最小合同自动派生" in prompt
    assert "如果系统接口数据包含毛利公式核对，明确说明计算净毛利与接口净毛利是否一致；不一致时提示复核上游金额字段或接口合同" in prompt
    assert "链路来源: 接口原生链路" in prompt
    assert "钱流链路：按乘客支付、平台抽成、司机收入、补贴、优惠、渠道费、净毛利说明，并交代链路来源（接口原生/自动派生）" in prompt
    assert "信息来源：列出工具选择来源/依据、系统接口、审计ID和文档编号" in prompt


def test_build_prompt_honors_explicit_answer_perspective(monkeypatch):
    module, _tracker, _cache_service = load_rag_module(monkeypatch)
    service = module.RAGService()

    prompt = service._build_prompt(
        query="运营看订单 ORD88888 的补贴是否异常",
        context="【文档 1】毛利口径说明",
        scene_type="profit",
        tool_context="平台净毛利 2.33 元，补贴 8 元。",
        answer_perspective="finance",
    )

    assert "主口径：财务口径" in prompt
    assert "重点区分收入、成本、补贴优惠、渠道费和平台净毛利" in prompt


def test_build_prompt_includes_tool_error_degradation_contract(monkeypatch):
    module, _tracker, _cache_service = load_rag_module(monkeypatch)
    service = module.RAGService()

    prompt = service._build_prompt(
        query="查询订单 ORD88888 的毛利链路",
        context="【文档 1】毛利口径说明",
        scene_type="profit",
        tool_context=(
            "【工具 1】订单毛利链路\n"
            "状态: error\n"
            "审计ID: bt-error123\n"
            "摘要: 订单毛利链路调用失败，请稍后重试或联系系统管理员。"
        ),
    )

    assert "状态: error" in prompt
    assert "实时接口未成功返回数据" in prompt
    assert "不要编造订单实时结论" in prompt
    assert "审计ID" in prompt


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
