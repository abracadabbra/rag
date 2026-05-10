"""
文本分块器单元测试
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


class FakeRecursiveCharacterTextSplitter:
    def __init__(self, chunk_size, chunk_overlap, separators, length_function):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators
        self.length_function = length_function

    def split_text(self, text):
        if not text:
            return []

        if self.chunk_size <= 0:
            return [text]

        step = max(1, self.chunk_size - self.chunk_overlap)
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(text_length, start + self.chunk_size)
            chunks.append(text[start:end])
            if end == text_length:
                break
            start += step

        return chunks


def load_splitters_module():
    """按文件路径加载 splitters 模块并注入假 langchain。"""
    fake_text_splitter_module = ModuleType("langchain.text_splitter")
    fake_text_splitter_module.RecursiveCharacterTextSplitter = FakeRecursiveCharacterTextSplitter
    fake_langchain_module = ModuleType("langchain")
    fake_langchain_module.text_splitter = fake_text_splitter_module

    sys.modules["langchain"] = fake_langchain_module
    sys.modules["langchain.text_splitter"] = fake_text_splitter_module

    module_path = Path(__file__).resolve().parents[1] / "ingestion" / "splitters.py"
    spec = importlib.util.spec_from_file_location("test_ingestion_splitters", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_text_splitter_uses_default_settings():
    module = load_splitters_module()

    splitter = module.TextSplitter()

    assert splitter.chunk_size == 500
    assert splitter.chunk_overlap == 50
    assert splitter.separators[0] == "\n\n"
    assert splitter.splitter.chunk_size == 500
    assert splitter.splitter.chunk_overlap == 50


def test_text_splitter_allows_custom_settings():
    module = load_splitters_module()

    splitter = module.TextSplitter(
        chunk_size=10,
        chunk_overlap=2,
        separators=["|", ""],
    )

    assert splitter.chunk_size == 10
    assert splitter.chunk_overlap == 2
    assert splitter.separators == ["|", ""]
    assert splitter.splitter.separators == ["|", ""]


def test_split_text_delegates_to_underlying_splitter():
    module = load_splitters_module()
    splitter = module.TextSplitter(chunk_size=5, chunk_overlap=1)

    chunks = splitter.split_text("ABCDEFGHIJK")

    assert chunks == ["ABCDE", "EFGHI", "IJK"]


def test_split_documents_preserves_metadata_and_adds_chunk_indices():
    module = load_splitters_module()
    splitter = module.TextSplitter(chunk_size=5, chunk_overlap=1)

    chunks = splitter.split_documents(
        [
            {
                "content": "ABCDEFGHIJK",
                "metadata": {"rule_id": "R001", "scene_type": "risk_rule"},
            }
        ]
    )

    assert chunks == [
        {
            "content": "ABCDE",
            "metadata": {
                "rule_id": "R001",
                "scene_type": "risk_rule",
                "chunk_index": 0,
                "total_chunks": 3,
            },
        },
        {
            "content": "EFGHI",
            "metadata": {
                "rule_id": "R001",
                "scene_type": "risk_rule",
                "chunk_index": 1,
                "total_chunks": 3,
            },
        },
        {
            "content": "IJK",
            "metadata": {
                "rule_id": "R001",
                "scene_type": "risk_rule",
                "chunk_index": 2,
                "total_chunks": 3,
            },
        },
    ]


def test_module_level_helpers_work():
    module = load_splitters_module()

    text_chunks = module.split_text("ABCDEFGHIJK")
    doc_chunks = module.split_documents(
        [{"content": "ABCDEFGHIJK", "metadata": {"source": "demo"}}]
    )

    assert len(text_chunks) >= 1
    assert doc_chunks[0]["metadata"]["source"] == "demo"
    assert doc_chunks[0]["metadata"]["chunk_index"] == 0
