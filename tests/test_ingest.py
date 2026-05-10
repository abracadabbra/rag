"""
数据摄入编排单元测试
"""

import importlib.util
import hashlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


class FakeCollection:
    def __init__(self, name, tracker):
        self.name = name
        self.tracker = tracker
        self.insert_calls = []
        self.flush_calls = 0

    def insert(self, rows):
        self.insert_calls.append(rows)
        if self.tracker.insert_error is not None:
            raise self.tracker.insert_error

    def flush(self):
        self.flush_calls += 1


def load_ingest_module(
    monkeypatch,
    *,
    loaded_documents=None,
    split_chunks=None,
    embeddings=None,
    insert_error=None,
):
    """按文件路径加载 ingest 模块并注入假依赖。"""

    tracker = SimpleNamespace(
        connect_calls=[],
        load_calls=[],
        split_calls=[],
        embed_calls=[],
        collection=None,
        insert_error=insert_error,
    )

    fake_click = ModuleType("click")

    def passthrough_decorator(*_args, **_kwargs):
        def decorator(func):
            return func
        return decorator

    fake_click.command = passthrough_decorator
    fake_click.option = passthrough_decorator
    fake_click.Choice = lambda values: values

    def fake_connect(**kwargs):
        tracker.connect_calls.append(kwargs)

    fake_pymilvus = ModuleType("pymilvus")
    fake_pymilvus.connections = SimpleNamespace(connect=fake_connect)

    def collection_factory(name):
        collection = FakeCollection(name, tracker)
        tracker.collection = collection
        return collection

    fake_pymilvus.Collection = collection_factory

    fake_loaders = ModuleType("ingestion.loaders")
    fake_loaders.load_documents = lambda paths: tracker.load_calls.append(paths) or list(loaded_documents or [])

    fake_splitters = ModuleType("ingestion.splitters")
    fake_splitters.split_documents = lambda docs: tracker.split_calls.append(docs) or list(split_chunks or [])

    fake_embeddings = ModuleType("ingestion.embeddings")
    fake_embeddings.embed_documents = lambda texts: tracker.embed_calls.append(texts) or list(embeddings or [])

    monkeypatch.setitem(sys.modules, "click", fake_click)
    monkeypatch.setitem(sys.modules, "pymilvus", fake_pymilvus)
    monkeypatch.setitem(sys.modules, "ingestion.loaders", fake_loaders)
    monkeypatch.setitem(sys.modules, "ingestion.splitters", fake_splitters)
    monkeypatch.setitem(sys.modules, "ingestion.embeddings", fake_embeddings)

    module_path = Path(__file__).resolve().parents[1] / "ingestion" / "ingest.py"
    spec = importlib.util.spec_from_file_location("test_ingestion_ingest", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, tracker


def test_ingest_directory_dry_run_skips_embedding_and_insert(monkeypatch, tmp_path):
    source_dir = tmp_path / "risk_rules"
    source_dir.mkdir()
    (source_dir / "R001.md").write_text("# demo", encoding="utf-8")

    loaded_documents = [{"content": "doc-1", "metadata": {"source": "R001.md"}}]
    split_chunks = [{"content": "chunk-1", "metadata": {"source": "R001.md"}}]
    module, tracker = load_ingest_module(
        monkeypatch,
        loaded_documents=loaded_documents,
        split_chunks=split_chunks,
    )

    ingestion = module.DataIngestion(collection_name="test_collection")
    stats = ingestion.ingest_directory(
        source_dir=str(source_dir),
        scene_type="risk_rule",
        dry_run=True,
    )

    assert stats == {"success": 1, "failed": 0, "skipped": 0}
    assert tracker.connect_calls[0]["alias"] == "default"
    assert tracker.load_calls[0] == [str(source_dir / "R001.md")]
    assert tracker.split_calls[0][0]["metadata"]["scene_type"] == "risk_rule"
    assert tracker.embed_calls == []
    assert tracker.collection.insert_calls == []
    assert tracker.collection.flush_calls == 0


def test_ingest_directory_full_flow_inserts_vectors(monkeypatch, tmp_path):
    source_dir = tmp_path / "risk_rules"
    source_dir.mkdir()
    (source_dir / "R001.md").write_text("# demo", encoding="utf-8")
    (source_dir / "R002.txt").write_text("demo", encoding="utf-8")

    loaded_documents = [
        {"content": "doc-1", "metadata": {"source": str(source_dir / "R001.md")}},
        {"content": "doc-2", "metadata": {"source": str(source_dir / "R002.txt")}},
    ]
    split_chunks = [
        {"content": "chunk-1", "metadata": {"source": str(source_dir / "R001.md"), "chunk_index": 0}},
        {"content": "chunk-2", "metadata": {"source": str(source_dir / "R002.txt"), "chunk_index": 1}},
    ]
    embeddings = [[0.1, 0.2], [0.3, 0.4]]
    module, tracker = load_ingest_module(
        monkeypatch,
        loaded_documents=loaded_documents,
        split_chunks=split_chunks,
        embeddings=embeddings,
    )

    ingestion = module.DataIngestion(collection_name="test_collection")
    stats = ingestion.ingest_directory(
        source_dir=str(source_dir),
        scene_type="risk_rule",
    )

    assert stats == {"success": 2, "failed": 0, "skipped": 0}
    assert tracker.embed_calls == [["chunk-1", "chunk-2"]]
    assert len(tracker.collection.insert_calls) == 1
    inserted = tracker.collection.insert_calls[0]
    assert inserted[1] == embeddings
    assert inserted[2] == ["risk_rule", "risk_rule"]
    assert inserted[3] == ["chunk-1", "chunk-2"]
    assert inserted[4] == [chunk["metadata"] for chunk in split_chunks]
    assert tracker.collection.flush_calls == 1


def test_ingest_directory_returns_zero_when_no_supported_files(monkeypatch, tmp_path):
    source_dir = tmp_path / "empty"
    source_dir.mkdir()
    (source_dir / "notes.csv").write_text("a,b", encoding="utf-8")
    module, _tracker = load_ingest_module(monkeypatch)

    ingestion = module.DataIngestion(collection_name="test_collection")
    stats = ingestion.ingest_directory(
        source_dir=str(source_dir),
        scene_type="risk_rule",
    )

    assert stats == {"success": 0, "failed": 0, "skipped": 0}


def test_ingest_directory_raises_for_missing_directory(monkeypatch, tmp_path):
    module, _tracker = load_ingest_module(monkeypatch)
    ingestion = module.DataIngestion(collection_name="test_collection")

    with pytest.raises(ValueError, match="目录不存在"):
        ingestion.ingest_directory(
            source_dir=str(tmp_path / "missing"),
            scene_type="risk_rule",
        )


def test_generate_id_uses_scene_source_and_chunk_index(monkeypatch):
    module, _tracker = load_ingest_module(monkeypatch)
    ingestion = module.DataIngestion(collection_name="test_collection")
    chunk = {
        "metadata": {
            "source": "data/risk_rules/R001.md",
            "chunk_index": 3,
        }
    }

    generated = ingestion._generate_id(chunk, "risk_rule", 99)
    expected = hashlib.md5("risk_rule_data/risk_rules/R001.md_3".encode()).hexdigest()

    assert generated == expected


def test_insert_to_milvus_returns_failed_stats_when_batch_insert_fails(monkeypatch):
    module, tracker = load_ingest_module(
        monkeypatch,
        insert_error=RuntimeError("insert failed"),
    )
    ingestion = module.DataIngestion(collection_name="test_collection")

    stats = ingestion._insert_to_milvus(
        chunks=[{"content": "chunk-1", "metadata": {"source": "a.md", "chunk_index": 0}}],
        embeddings=[[0.1, 0.2]],
        scene_type="risk_rule",
    )

    assert stats == {"success": 0, "failed": 1, "skipped": 0}
    assert len(tracker.collection.insert_calls) == 1
