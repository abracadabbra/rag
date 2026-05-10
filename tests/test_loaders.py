"""
文档加载器单元测试
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load_loaders_module(monkeypatch):
    """在无真实 yaml 依赖下按文件路径加载 loaders 模块。"""

    fake_yaml = ModuleType("yaml")

    def safe_load(text):
        result = {}
        current_nested_key = None

        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            if not line.strip():
                continue

            if line.startswith("  ") and current_nested_key:
                nested_key, value = line.strip().split(":", 1)
                result[current_nested_key][nested_key.strip()] = value.strip()
                continue

            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if value:
                result[key] = value
                current_nested_key = None
            else:
                result[key] = {}
                current_nested_key = key

        return result

    fake_yaml.safe_load = safe_load
    monkeypatch.setitem(sys.modules, "yaml", fake_yaml)

    module_path = Path(__file__).resolve().parents[1] / "ingestion" / "loaders.py"
    spec = importlib.util.spec_from_file_location("test_ingestion_loaders", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_extract_and_remove_frontmatter(monkeypatch):
    module = load_loaders_module(monkeypatch)
    loader = module.MarkdownLoader()
    content = """---
metadata:
  rule_id: R001
  rule_name: 信用卡交易限额规则
---

# 标题

正文内容
"""

    metadata = loader._extract_frontmatter(content)
    cleaned = loader._remove_frontmatter(content)

    assert metadata == {
        "rule_id": "R001",
        "rule_name": "信用卡交易限额规则",
    }
    assert cleaned == "# 标题\n\n正文内容"


def test_markdown_loader_load_includes_file_metadata(monkeypatch, tmp_path):
    module = load_loaders_module(monkeypatch)
    file_path = tmp_path / "R001_信用卡交易限额.md"
    file_path.write_text(
        """---
rule_id: R001
rule_name: 信用卡交易限额规则
---

白金卡单笔限额 50,000 元
""",
        encoding="utf-8",
    )

    document = module.MarkdownLoader().load(str(file_path))

    assert document["content"] == "白金卡单笔限额 50,000 元"
    assert document["metadata"]["rule_id"] == "R001"
    assert document["metadata"]["rule_name"] == "信用卡交易限额规则"
    assert document["metadata"]["source"] == str(file_path)
    assert document["metadata"]["file_name"] == file_path.name
    assert document["metadata"]["file_type"] == "markdown"


def test_text_loader_load(monkeypatch, tmp_path):
    module = load_loaders_module(monkeypatch)
    file_path = tmp_path / "notes.txt"
    file_path.write_text("普通文本内容", encoding="utf-8")

    document = module.TextLoader().load(str(file_path))

    assert document == {
        "content": "普通文本内容",
        "metadata": {
            "source": str(file_path),
            "file_name": "notes.txt",
            "file_type": "txt",
        },
    }


def test_get_loader_returns_expected_loader_types(monkeypatch):
    module = load_loaders_module(monkeypatch)

    assert isinstance(module.get_loader("a.md"), module.MarkdownLoader)
    assert isinstance(module.get_loader("a.markdown"), module.MarkdownLoader)
    assert isinstance(module.get_loader("a.txt"), module.TextLoader)


def test_get_loader_raises_for_unsupported_extension(monkeypatch):
    module = load_loaders_module(monkeypatch)

    try:
        module.get_loader("a.csv")
    except ValueError as exc:
        assert "不支持的文件格式" in str(exc)
    else:
        raise AssertionError("expected ValueError for unsupported extension")


def test_load_documents_skips_failures_and_keeps_successes(monkeypatch, tmp_path):
    module = load_loaders_module(monkeypatch)
    good_file = tmp_path / "good.txt"
    good_file.write_text("hello", encoding="utf-8")
    bad_file = tmp_path / "bad.csv"
    bad_file.write_text("not supported", encoding="utf-8")

    documents = module.load_documents([str(good_file), str(bad_file)])

    assert len(documents) == 1
    assert documents[0]["content"] == "hello"
