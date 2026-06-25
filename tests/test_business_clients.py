"""
Business client tests.
"""

import json
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from api.services import business_clients
from api.services.business_contracts import (
    BUSINESS_TOOL_ENDPOINT_TEMPLATES,
    BUSINESS_TOOL_RESULT_ALLOWLIST,
    BusinessContractError,
    derive_profit_chain,
    PROFIT_CHAIN_TERMINAL_NODE,
    PROFIT_REQUIRED_FIELDS,
    PROFIT_TOOL_NAME,
    RISK_REQUIRED_FIELDS,
    RISK_TOOL_NAME,
    contract_snapshot,
)
from api.services.business_clients import (
    ProfitSystemClient,
    RiskSystemClient,
    validate_business_response,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class FakeRawResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload.encode("utf-8")


def make_risk_payload(order_id="ORD12345"):
    return {
        "order_id": order_id,
        "decision": "pass",
        "risk_score": 12,
        "hit_rules": [
            {
                "rule_id": "RISK-low-001",
                "rule_name": "低风险订单",
                "evidence": "未命中高危规则",
            }
        ],
        "recommended_action": "建议放行。",
    }


def make_profit_payload(order_id="ORD88888"):
    return {
        "order_id": order_id,
        "gross_amount": 100.0,
        "platform_commission": 15.0,
        "driver_income": 82.0,
        "subsidy": 3.0,
        "coupon": 2.0,
        "platform_net_profit": 8.0,
        "chain": [
            {"node": "乘客支付", "amount": 100.0},
            {"node": "平台抽成", "amount": 15.0},
            {"node": "平台净毛利", "amount": 8.0},
        ],
    }


def test_risk_client_uses_http_when_base_url_configured(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append({"req": req, "timeout": timeout})
        return FakeResponse(make_risk_payload())

    monkeypatch.setattr("api.services.business_clients.request.urlopen", fake_urlopen)

    client = RiskSystemClient(
        base_url="https://risk.example.test/api",
        api_key="risk-token",
        timeout=3,
    )
    result = client.get_event_detail("ORD12345")

    assert result["order_id"] == "ORD12345"
    assert result["decision"] == "pass"
    assert result["risk_score"] == 12
    assert calls[0]["timeout"] == 3
    assert calls[0]["req"].full_url == "https://risk.example.test/api/risk/events/ORD12345"
    assert calls[0]["req"].headers["Authorization"] == "Bearer risk-token"


def test_profit_client_uses_http_when_base_url_configured(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append({"req": req, "timeout": timeout})
        return FakeResponse(make_profit_payload())

    monkeypatch.setattr("api.services.business_clients.request.urlopen", fake_urlopen)

    client = ProfitSystemClient(
        base_url="https://profit.example.test",
        api_key="",
        timeout=4,
    )
    result = client.get_chain_detail("ORD88888")

    assert result["order_id"] == "ORD88888"
    assert result["driver_income"] == 82.0
    assert result["platform_net_profit"] == 8.0
    assert calls[0]["timeout"] == 4
    assert calls[0]["req"].full_url == "https://profit.example.test/profit/orders/ORD88888/chain"
    assert "Authorization" not in calls[0]["req"].headers


def test_risk_http_response_must_match_contract(monkeypatch):
    def fake_urlopen(_req, timeout):
        payload = make_risk_payload()
        del payload["recommended_action"]
        return FakeResponse(payload)

    monkeypatch.setattr("api.services.business_clients.request.urlopen", fake_urlopen)

    client = RiskSystemClient(base_url="https://risk.example.test")

    with pytest.raises(
        BusinessContractError,
        match="missing required fields: recommended_action",
    ) as exc_info:
        client.get_event_detail("ORD12345")

    assert exc_info.value.diagnostic_code == "missing_required_fields"
    assert exc_info.value.missing_fields == ["recommended_action"]
    assert exc_info.value.invalid_fields == []


def test_profit_http_chain_must_match_contract(monkeypatch):
    def fake_urlopen(_req, timeout):
        payload = make_profit_payload()
        payload["chain"] = [{"node": "平台抽成", "amount": "15.0"}]
        return FakeResponse(payload)

    monkeypatch.setattr("api.services.business_clients.request.urlopen", fake_urlopen)

    client = ProfitSystemClient(base_url="https://profit.example.test")

    with pytest.raises(
        BusinessContractError,
        match=r"chain\[1\]\.amount expected number",
    ) as exc_info:
        client.get_chain_detail("ORD88888")

    assert exc_info.value.diagnostic_code == "invalid_chain"
    assert exc_info.value.missing_fields == []
    assert exc_info.value.invalid_fields == ["chain[1].amount expected number"]


def test_http_response_must_be_json_object(monkeypatch):
    def fake_urlopen(_req, timeout):
        return FakeResponse([make_profit_payload()])

    monkeypatch.setattr("api.services.business_clients.request.urlopen", fake_urlopen)

    client = ProfitSystemClient(base_url="https://profit.example.test")

    with pytest.raises(
        BusinessContractError,
        match="Business API returned non-object JSON",
    ) as exc_info:
        client.get_chain_detail("ORD88888")

    assert exc_info.value.diagnostic_code == "non_object_json"
    assert exc_info.value.missing_fields == []
    assert exc_info.value.invalid_fields == []


def test_http_response_must_be_valid_json(monkeypatch):
    def fake_urlopen(_req, timeout):
        return FakeRawResponse("{not valid json")

    monkeypatch.setattr("api.services.business_clients.request.urlopen", fake_urlopen)

    client = ProfitSystemClient(base_url="https://profit.example.test")

    with pytest.raises(
        BusinessContractError,
        match="Business API returned invalid JSON",
    ) as exc_info:
        client.get_chain_detail("ORD88888")

    assert exc_info.value.diagnostic_code == "invalid_json"
    assert exc_info.value.missing_fields == []
    assert exc_info.value.invalid_fields == ["response body invalid JSON"]


@pytest.mark.parametrize("status_code", [401, 500])
def test_http_status_errors_are_wrapped_without_sensitive_details(
    monkeypatch,
    status_code,
):
    sensitive_url = "https://profit.example.test/profit/orders/ORD88888/chain?token=secret"

    def fake_urlopen(_req, timeout):
        raise HTTPError(
            url=sensitive_url,
            code=status_code,
            msg="Unauthorized token=secret",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr("api.services.business_clients.request.urlopen", fake_urlopen)

    client = ProfitSystemClient(base_url="https://profit.example.test", api_key="secret")

    with pytest.raises(ConnectionError) as exc_info:
        client.get_chain_detail("ORD88888")

    message = str(exc_info.value)
    assert message == f"Business API HTTP error: status={status_code}"
    assert "secret" not in message
    assert "ORD88888" not in message
    assert "profit.example.test" not in message


def test_url_errors_are_wrapped_without_sensitive_details(monkeypatch):
    def fake_urlopen(_req, timeout):
        raise URLError("dns failed for profit.example.test with token=secret")

    monkeypatch.setattr("api.services.business_clients.request.urlopen", fake_urlopen)

    client = ProfitSystemClient(base_url="https://profit.example.test", api_key="secret")

    with pytest.raises(ConnectionError) as exc_info:
        client.get_chain_detail("ORD88888")

    message = str(exc_info.value)
    assert message == "Business API connection failed"
    assert "secret" not in message
    assert "profit.example.test" not in message
    assert "ORD88888" not in message


def test_timeouts_are_wrapped_without_sensitive_details(monkeypatch):
    def fake_urlopen(_req, timeout):
        raise TimeoutError("timed out reading token=secret for ORD88888")

    monkeypatch.setattr("api.services.business_clients.request.urlopen", fake_urlopen)

    client = ProfitSystemClient(base_url="https://profit.example.test", api_key="secret")

    with pytest.raises(TimeoutError) as exc_info:
        client.get_chain_detail("ORD88888")

    message = str(exc_info.value)
    assert message == "Business API request timed out"
    assert "secret" not in message
    assert "ORD88888" not in message


def test_validate_business_response_reuses_risk_contract():
    payload = make_risk_payload()

    result = validate_business_response(RISK_TOOL_NAME, payload)

    assert result["order_id"] == "ORD12345"
    assert result["hit_rules"][0]["rule_id"] == "RISK-low-001"


def test_validate_business_response_reports_profit_contract_diagnostics():
    payload = make_profit_payload()
    payload["platform_net_profit"] = "8.0"

    with pytest.raises(
        BusinessContractError,
        match="platform_net_profit expected number",
    ) as exc_info:
        validate_business_response(PROFIT_TOOL_NAME, payload)

    assert exc_info.value.diagnostic_code == "invalid_field_types"
    assert exc_info.value.invalid_fields == ["platform_net_profit expected number"]


def test_validate_business_response_requires_object_payload():
    with pytest.raises(
        BusinessContractError,
        match="Business API returned non-object JSON",
    ) as exc_info:
        validate_business_response(PROFIT_TOOL_NAME, [make_profit_payload()])

    assert exc_info.value.diagnostic_code == "non_object_json"


def test_clients_fallback_to_mock_without_base_url():
    risk_result = RiskSystemClient(base_url="").get_event_detail("ORD12345")
    profit_result = ProfitSystemClient(base_url="").get_chain_detail("ORD88888")

    assert risk_result["order_id"] == "ORD12345"
    assert risk_result["decision"] == "block"
    assert profit_result["order_id"] == "ORD88888"
    assert profit_result["driver_income"] > 0
    assert "chain_source" not in profit_result
    assert profit_result["chain"][-1]["node"] == PROFIT_CHAIN_TERMINAL_NODE
    assert profit_result["chain"][-1]["amount"] == profit_result["platform_net_profit"]
    assert profit_result["chain"][-1]["role"] == "经营结果"


def test_business_clients_use_shared_contract_constants():
    snapshot = contract_snapshot()

    assert business_clients.RISK_REQUIRED_FIELDS is RISK_REQUIRED_FIELDS
    assert business_clients.PROFIT_REQUIRED_FIELDS is PROFIT_REQUIRED_FIELDS
    assert business_clients.endpoint_path(
        RISK_TOOL_NAME,
        order_id="ORD12345",
    ) == BUSINESS_TOOL_ENDPOINT_TEMPLATES[RISK_TOOL_NAME].format(order_id="ORD12345")
    assert business_clients.endpoint_path(
        PROFIT_TOOL_NAME,
        order_id="ORD88888",
    ) == BUSINESS_TOOL_ENDPOINT_TEMPLATES[PROFIT_TOOL_NAME].format(order_id="ORD88888")
    assert snapshot["risk"]["tool_name"] == RISK_TOOL_NAME
    assert snapshot["prompt_contract"]["profit"]["name"] == "毛利抽成"
    assert snapshot["prompt_contract"]["risk_rule"]["answer_perspectives"]["strategy"]["label"] == "风控策略口径"
    assert snapshot["risk"]["request_json_schema"]["required"] == ["order_id"]
    assert snapshot["risk"]["response_json_schema"]["properties"]["risk_score"]["type"] == "number"
    assert snapshot["risk"]["response_json_schema"]["properties"]["hit_rules"]["items"][
        "required"
    ] == ["rule_id", "rule_name", "evidence"]
    assert snapshot["risk"]["field_catalog"][0]["name"] == "order_id"
    assert snapshot["risk"]["field_catalog"][1]["label"] == "系统决策"
    assert snapshot["profit"]["tool_name"] == PROFIT_TOOL_NAME
    assert snapshot["profit"]["request_json_schema"]["required"] == ["order_id"]
    assert snapshot["profit"]["response_json_schema"]["properties"]["platform_net_profit"][
        "type"
    ] == "number"
    assert snapshot["profit"]["response_json_schema"]["properties"]["chain"]["items"][
        "required"
    ] == ["node", "amount"]
    assert "chain_source" not in snapshot["profit"]["response_json_schema"]["properties"]
    assert snapshot["profit"]["chain_step_optional_fields"] == {
        "source_field": "str",
        "role": "str",
        "tone": "str",
        "note": "str",
    }
    assert snapshot["profit"]["chain_terminal_node"] == PROFIT_CHAIN_TERMINAL_NODE
    assert snapshot["profit"]["derived_chain_steps"][0] == {
        "node": "乘客支付",
        "field": "gross_amount",
        "sign": 1,
        "required": True,
        "role": "订单收入",
        "tone": "income",
        "note": "乘客实付基数",
    }
    assert snapshot["profit"]["display_metadata_fields"] == [
        {
            "name": "chain_source",
            "label": "链路来源",
            "type": "string",
            "required": False,
            "description": "后端展示元信息，用于标记当前链路为真实接口原生返回(api)还是按最小合同自动派生(derived)。",
        }
    ]
    assert snapshot["profit"]["derived_chain_steps"][-1]["node"] == PROFIT_CHAIN_TERMINAL_NODE
    assert snapshot["profit"]["field_catalog"][7]["name"] == "platform_net_profit"
    assert "platform_net_profit" in BUSINESS_TOOL_RESULT_ALLOWLIST[PROFIT_TOOL_NAME]
    assert "chain_source" in BUSINESS_TOOL_RESULT_ALLOWLIST[PROFIT_TOOL_NAME]
    assert snapshot["integration_handoff"]["recommended_sequence"] == [
        "export_contracts",
        "validate_captured_samples",
        "fake_http_acceptance",
        "external_http_strict_gate",
        "frontend_evidence_check",
    ]
    assert snapshot["integration_handoff"]["commands"]["export_contracts"] == (
        "make business-contracts"
    )
    assert "external_http_configured" in snapshot["integration_handoff"]["go_live_gates"]
    assert "captured_sample_validation" in snapshot["integration_handoff"]["go_live_gates"]
    assert (
        snapshot["integration_handoff"]["integration_modes"]["fake_http"]
        == "In-process fake transport exercises the HTTP client path; not a production rollout."
    )
    assert any(
        "Fake HTTP acceptance cannot replace" in note
        for note in snapshot["integration_handoff"]["safety_notes"]
    )


def test_business_contract_export_cli_matches_shared_snapshot(tmp_path):
    output_file = tmp_path / "business-tool-contracts.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/export_business_contracts.py",
            "--output",
            str(output_file),
        ],
        check=False,
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "Wrote business tool contracts to" in completed.stderr
    assert json.loads(output_file.read_text(encoding="utf-8")) == contract_snapshot()

    stdout_completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/export_business_contracts.py",
            "--compact",
        ],
        check=False,
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )

    assert stdout_completed.returncode == 0
    assert json.loads(stdout_completed.stdout) == contract_snapshot()


def test_derive_profit_chain_from_minimum_contract_fields():
    chain = derive_profit_chain(
        {
            "order_id": "ORD88888",
            "gross_amount": 128.6,
            "platform_commission": 19.29,
            "driver_income": 92.35,
            "subsidy": 8.0,
            "coupon": 6.0,
            "platform_net_profit": 5.29,
        }
    )

    assert chain == [
        {
            "node": "乘客支付",
            "amount": 128.6,
            "source_field": "gross_amount",
            "role": "订单收入",
            "tone": "income",
            "note": "乘客实付基数",
        },
        {
            "node": "平台抽成",
            "amount": 19.29,
            "source_field": "platform_commission",
            "role": "平台收入",
            "tone": "income",
            "note": "收入进入毛利公式",
        },
        {
            "node": "司机收入",
            "amount": 92.35,
            "source_field": "driver_income",
            "role": "司机结算",
            "tone": "payout",
            "note": "履约侧结算",
        },
        {
            "node": "平台补贴",
            "amount": -8.0,
            "source_field": "subsidy",
            "role": "平台成本",
            "tone": "cost",
            "note": "平台承担成本",
        },
        {
            "node": "用户优惠",
            "amount": -6.0,
            "source_field": "coupon",
            "role": "营销成本",
            "tone": "cost",
            "note": "优惠消耗抽成",
        },
        {
            "node": "平台净毛利",
            "amount": 5.29,
            "source_field": "platform_net_profit",
            "role": "经营结果",
            "tone": "net",
            "note": "最终留存",
        },
    ]


def test_derive_profit_chain_includes_optional_channel_fee_when_available():
    chain = derive_profit_chain(
        {
            "gross_amount": 128.6,
            "platform_commission": 19.29,
            "driver_income": 92.35,
            "subsidy": 8.0,
            "coupon": 6.0,
            "channel_fee": 2.96,
            "platform_net_profit": 2.33,
        }
    )

    assert {
        "node": "渠道成本",
        "amount": -2.96,
        "source_field": "channel_fee",
        "role": "渠道成本",
        "tone": "cost",
        "note": "获客/支付渠道成本",
    } in chain
    assert chain[-1] == {
        "node": "平台净毛利",
        "amount": 2.33,
        "source_field": "platform_net_profit",
        "role": "经营结果",
        "tone": "net",
        "note": "最终留存",
    }


def test_derive_profit_chain_returns_empty_when_required_amount_is_missing():
    chain = derive_profit_chain(
        {
            "gross_amount": 128.6,
            "platform_commission": 19.29,
            "driver_income": 92.35,
            "subsidy": 8.0,
            "coupon": 6.0,
        }
    )

    assert chain == []
