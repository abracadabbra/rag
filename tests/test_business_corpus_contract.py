"""
Business corpus contract tests.

These checks keep the local retrieval corpus aligned with the business tool
contracts so risk/profit answers can cite domain documents after ingestion.
"""

from pathlib import Path
import importlib.util
import sys
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
RISK_DOC = ROOT / "data/risk_rules/R020_订单风控事件解释口径.md"
PROFIT_DOC = ROOT / "data/profit/P001_订单毛利链路分析口径.md"


def load_loaders_module(monkeypatch):
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
                result[current_nested_key][nested_key.strip()] = value.strip().strip('"')
                continue

            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"')

            if value:
                result[key] = value
                current_nested_key = None
            else:
                result[key] = {}
                current_nested_key = key

        return result

    fake_yaml.safe_load = safe_load
    monkeypatch.setitem(sys.modules, "yaml", fake_yaml)

    module_path = ROOT / "ingestion/loaders.py"
    spec = importlib.util.spec_from_file_location("test_business_corpus_loaders", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_profit_corpus_contains_money_flow_contract_document():
    source = PROFIT_DOC.read_text(encoding="utf-8")

    assert 'rule_id: "P001"' in source
    assert 'scene_type: "profit"' in source
    assert "乘客支付 -> 平台抽成 -> 司机收入 -> 平台补贴 -> 用户优惠 -> 渠道成本 -> 平台净毛利" in source
    assert "`gross_amount`" in source
    assert "`platform_commission`" in source
    assert "`driver_income`" in source
    assert "`subsidy`" in source
    assert "`coupon`" in source
    assert "`channel_fee`" in source
    assert "`platform_net_profit`" in source
    assert "乘客支付不是平台净收入" in source
    assert "补贴金额高于平台抽成的 50%" in source


def test_risk_corpus_contains_order_event_explanation_document():
    source = RISK_DOC.read_text(encoding="utf-8")

    assert 'rule_id: "R020"' in source
    assert 'scene_type: "risk_rule"' in source
    assert "`decision`" in source
    assert "`risk_score`" in source
    assert "`hit_rules`" in source
    assert "`recommended_action`" in source
    assert "短时间多次高额交易" in source
    assert "新设备异常登录后交易" in source
    assert "风控结论" in source
    assert "证据边界" in source


def test_readme_documents_risk_and_profit_ingestion_commands():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    profit_readme = (ROOT / "data/profit/README.md").read_text(encoding="utf-8")
    risk_readme = (ROOT / "data/risk_rules/README.md").read_text(encoding="utf-8")

    assert "python -m ingestion.ingest --source data/risk_rules --scene risk_rule" in readme
    assert "python -m ingestion.ingest --source data/profit --scene profit" in readme
    assert "python -m ingestion.ingest --source data/profit --scene profit" in profit_readme
    assert "python -m ingestion.ingest --source data/risk_rules --scene risk_rule" in risk_readme


def test_business_corpus_frontmatter_is_parseable_by_markdown_loader(monkeypatch):
    module = load_loaders_module(monkeypatch)
    loader = module.MarkdownLoader()

    risk_doc = loader.load(str(RISK_DOC))
    profit_doc = loader.load(str(PROFIT_DOC))

    assert risk_doc["metadata"]["rule_id"] == "R020"
    assert risk_doc["metadata"]["scene_type"] == "risk_rule"
    assert risk_doc["metadata"]["rule_name"] == "订单风控事件解释口径"
    assert "订单级风控事件" in risk_doc["content"]
    assert "系统接口返回的订单级风控事件数据" in risk_doc["content"]

    assert profit_doc["metadata"]["rule_id"] == "P001"
    assert profit_doc["metadata"]["scene_type"] == "profit"
    assert profit_doc["metadata"]["rule_name"] == "订单毛利链路分析口径"
    assert "订单毛利链路" in profit_doc["content"]
    assert "乘客支付不是平台净收入" in profit_doc["content"]
