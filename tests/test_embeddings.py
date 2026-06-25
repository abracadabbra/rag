"""
Embedding 模块单元测试
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace


class FakeDenseRow:
    def __init__(self, row):
        self.row = row

    def tolist(self):
        return self.row


class FakeDenseVectors:
    def __init__(self, rows):
        self.rows = rows

    def tolist(self):
        return self.rows

    def __getitem__(self, index):
        return FakeDenseRow(self.rows[index])


def load_embeddings_module(monkeypatch):
    """按文件路径加载 embeddings 模块并注入假模型依赖。"""

    tracker = SimpleNamespace(
        bge_init_calls=[],
        bge_encode_calls=[],
        openai_init_calls=[],
        openai_embedding_calls=[],
    )

    class FakeBGEM3FlagModel:
        def __init__(self, model_name, use_fp16):
            tracker.bge_init_calls.append(
                {"model_name": model_name, "use_fp16": use_fp16}
            )

        def encode(self, texts, batch_size, max_length):
            tracker.bge_encode_calls.append(
                {
                    "texts": list(texts),
                    "batch_size": batch_size,
                    "max_length": max_length,
                }
            )
            dense = FakeDenseVectors(
                [[float(i + 1), float(i + 2)] for i, _text in enumerate(texts)]
            )
            return {"dense_vecs": dense}

    class FakeOpenAI:
        def __init__(self, api_key=None):
            tracker.openai_init_calls.append({"api_key": api_key})
            self.embeddings = SimpleNamespace(create=self._create)

        def _create(self, input, model):
            tracker.openai_embedding_calls.append(
                {"input": list(input), "model": model}
            )
            return SimpleNamespace(
                data=[
                    SimpleNamespace(embedding=[float(i), float(i) + 0.5])
                    for i, _item in enumerate(input, start=1)
                ]
            )

    fake_flag_embedding = ModuleType("FlagEmbedding")
    fake_flag_embedding.BGEM3FlagModel = FakeBGEM3FlagModel

    fake_openai = ModuleType("openai")
    fake_openai.OpenAI = FakeOpenAI

    fake_numpy = ModuleType("numpy")

    monkeypatch.setitem(sys.modules, "FlagEmbedding", fake_flag_embedding)
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)

    module_path = Path(__file__).resolve().parents[1] / "ingestion" / "embeddings.py"
    spec = importlib.util.spec_from_file_location("test_ingestion_embeddings", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, tracker


def test_bge_embedding_document_and_query_generation(monkeypatch):
    module, tracker = load_embeddings_module(monkeypatch)
    embedding = module.BGEEmbedding(
        model_name="BAAI/bge-m3",
        device="cuda",
        batch_size=8,
    )

    docs = embedding.embed_documents(["文本1", "文本2"])
    query = embedding.embed_query("查询")

    assert tracker.bge_init_calls == [
        {"model_name": "BAAI/bge-m3", "use_fp16": True}
    ]
    assert tracker.bge_encode_calls[0] == {
        "texts": ["文本1", "文本2"],
        "batch_size": 8,
        "max_length": 8192,
    }
    assert tracker.bge_encode_calls[1] == {
        "texts": ["查询"],
        "batch_size": 1,
        "max_length": 8192,
    }
    assert docs == [[1.0, 2.0], [2.0, 3.0]]
    assert query == [1.0, 2.0]


def test_openai_embedding_document_and_query_generation(monkeypatch):
    module, tracker = load_embeddings_module(monkeypatch)
    embedding = module.OpenAIEmbedding(
        model="text-embedding-3-small",
        api_key="test-key",
    )

    docs = embedding.embed_documents(["文本1", "文本2"])
    query = embedding.embed_query("查询")

    assert tracker.openai_init_calls == [{"api_key": "test-key"}]
    assert tracker.openai_embedding_calls[0] == {
        "input": ["文本1", "文本2"],
        "model": "text-embedding-3-small",
    }
    assert tracker.openai_embedding_calls[1] == {
        "input": ["查询"],
        "model": "text-embedding-3-small",
    }
    assert docs == [[1.0, 1.5], [2.0, 2.5]]
    assert query == [1.0, 1.5]


def test_get_embedding_generator_respects_openai_toggle(monkeypatch):
    module, tracker = load_embeddings_module(monkeypatch)
    module.get_embedding_generator.cache_clear()

    monkeypatch.setattr(module.settings, "use_deterministic_embedding", False)
    monkeypatch.setattr(module.settings, "use_sentence_transformer", False)
    monkeypatch.setattr(module.settings, "use_openai_embedding", True)
    monkeypatch.setattr(module.settings, "openai_embedding_model", "text-embedding-3-small")
    monkeypatch.setattr(module.settings, "openai_api_key", "openai-key")

    generator = module.get_embedding_generator()

    assert generator.__class__.__name__ == "OpenAIEmbedding"
    assert tracker.openai_init_calls == [{"api_key": "openai-key"}]

    module.get_embedding_generator.cache_clear()
    monkeypatch.setattr(module.settings, "use_deterministic_embedding", False)
    monkeypatch.setattr(module.settings, "use_sentence_transformer", False)
    monkeypatch.setattr(module.settings, "use_openai_embedding", False)
    monkeypatch.setattr(module.settings, "embedding_model", "BAAI/bge-m3")
    monkeypatch.setattr(module.settings, "embedding_device", "cpu")
    monkeypatch.setattr(module.settings, "embedding_batch_size", 16)

    generator = module.get_embedding_generator()

    assert generator.__class__.__name__ == "BGEEmbedding"
    assert tracker.bge_init_calls[-1] == {
        "model_name": "BAAI/bge-m3",
        "use_fp16": False,
    }


def test_deterministic_embedding_is_stable_and_dimensioned(monkeypatch):
    module, _tracker = load_embeddings_module(monkeypatch)

    embedding = module.DeterministicEmbedding(dimension=6)

    first = embedding.embed_query("订单 ORD88888")
    second = embedding.embed_query("订单 ORD88888")
    other = embedding.embed_query("订单 ORD99999")
    docs = embedding.embed_documents(["订单 ORD88888", "订单 ORD99999"])

    assert first == second
    assert first != other
    assert len(first) == 6
    assert docs == [first, other]
    assert round(sum(value * value for value in first), 6) == 1.0


def test_get_embedding_generator_prefers_deterministic_toggle(monkeypatch):
    module, tracker = load_embeddings_module(monkeypatch)
    module.get_embedding_generator.cache_clear()

    monkeypatch.setattr(module.settings, "use_deterministic_embedding", True)
    monkeypatch.setattr(module.settings, "deterministic_embedding_dimension", 7)
    monkeypatch.setattr(module.settings, "use_openai_embedding", True)
    monkeypatch.setattr(module.settings, "use_sentence_transformer", True)

    generator = module.get_embedding_generator()

    assert generator.__class__.__name__ == "DeterministicEmbedding"
    assert generator.dimension == 7
    assert tracker.openai_init_calls == []
    assert tracker.bge_init_calls == []


def test_module_level_helpers_delegate_to_cached_generator(monkeypatch):
    module, _tracker = load_embeddings_module(monkeypatch)

    class FakeGenerator:
        def __init__(self):
            self.doc_calls = []
            self.query_calls = []

        def embed_documents(self, texts):
            self.doc_calls.append(list(texts))
            return [[9.0, 9.5]]

        def embed_query(self, text):
            self.query_calls.append(text)
            return [8.0, 8.5]

    fake_generator = FakeGenerator()
    monkeypatch.setattr(module, "get_embedding_generator", lambda: fake_generator)

    docs = module.embed_documents(["文本A"])
    query = module.embed_query("问题A")

    assert docs == [[9.0, 9.5]]
    assert query == [8.0, 8.5]
    assert fake_generator.doc_calls == [["文本A"]]
    assert fake_generator.query_calls == ["问题A"]
