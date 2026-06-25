"""
Business tool smoke script tests.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from api.services.business_contracts import fake_profit_payload, fake_risk_payload
from scripts import business_tool_acceptance_pack
from scripts.business_tool_acceptance_pack import build_acceptance_pack
from scripts.business_tool_smoke import run_smoke
from scripts.validate_business_response_samples import validate_response_samples

MAKEFILE = Path("Makefile")
README = Path("README.md")
BUSINESS_TOOLS_DOC = Path("docs/BUSINESS_TOOLS.md")
BUSINESS_QUICKSTART_DOC = Path("docs/BUSINESS_TOOL_QUICKSTART.md")
RISK_SAMPLE_FILE = Path("examples/business_tool_samples/risk_response.sample.json")
PROFIT_SAMPLE_FILE = Path("examples/business_tool_samples/profit_response.sample.json")


def smoke_cli_env() -> dict[str, str]:
    """Force subprocess smoke checks to start from mock runtime defaults."""
    env = os.environ.copy()
    env.update(
        {
            "ENABLE_BUSINESS_TOOLS": "true",
            "BUSINESS_TOOL_TIMEOUT": "5",
            "ENABLE_BUSINESS_TOOL_LLM_INTENT": "false",
            "BUSINESS_TOOL_LLM_INTENT_MIN_CONFIDENCE": "0.75",
            "ENABLE_BUSINESS_TOOL_ACCESS_CONTROL": "false",
            "ENABLE_BUSINESS_TOOL_AUDIT_FILE": "false",
            "BUSINESS_TOOL_AUDIT_FILE": "logs/business_tool_audit.jsonl",
            "BUSINESS_TOOL_ACCESS_TOKEN": "",
            "BUSINESS_TOOL_READ_TOKEN": "",
            "BUSINESS_TOOL_EXECUTE_TOKEN": "",
            "RISK_API_BASE_URL": "",
            "RISK_API_KEY": "",
            "PROFIT_API_BASE_URL": "",
            "PROFIT_API_KEY": "",
        }
    )
    return env


@pytest.fixture(autouse=True)
def isolate_business_tool_runtime():
    """Keep in-process smoke tests independent from local .env runtime settings."""
    from api.config import settings
    from api.services.business_clients import reset_business_clients
    from api.services.tool_service import reset_tool_service

    business_fields = {
        "enable_business_tools": True,
        "business_tool_timeout": 5,
        "enable_business_tool_llm_intent": False,
        "business_tool_llm_intent_min_confidence": 0.75,
        "enable_business_tool_access_control": False,
        "business_tool_access_token": "",
        "business_tool_read_token": "",
        "business_tool_execute_token": "",
        "enable_business_tool_audit_file": False,
        "business_tool_audit_file": "logs/business_tool_audit.jsonl",
        "risk_api_base_url": "",
        "risk_api_key": "",
        "profit_api_base_url": "",
        "profit_api_key": "",
    }
    original_values = {
        field: getattr(settings, field) for field in business_fields
    }

    for field, value in business_fields.items():
        setattr(settings, field, value)
    reset_business_clients()
    reset_tool_service()

    try:
        yield
    finally:
        for field, value in original_values.items():
            setattr(settings, field, value)
        reset_business_clients()
        reset_tool_service()


def test_business_smoke_make_target_is_documented():
    makefile = MAKEFILE.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    doc = BUSINESS_TOOLS_DOC.read_text(encoding="utf-8")
    quickstart_doc = BUSINESS_QUICKSTART_DOC.read_text(encoding="utf-8")
    acceptance_doc = Path("docs/BUSINESS_TOOL_ACCEPTANCE.md").read_text(encoding="utf-8")

    assert "business-smoke" in makefile
    assert "business-llm-acceptance" in makefile
    assert "VENV_DIR ?= .venv" in makefile
    assert "PYTHON_BIN ?= $(shell if [ -x ./$(VENV_DIR)/bin/python ]" in makefile
    assert "venv/bin/activate" not in makefile
    assert "python3 -m venv $(VENV_DIR)" in makefile
    assert "$(VENV_DIR)/bin/python -m pip install -r requirements.txt" in makefile
    assert "$(PYTHON_BIN) -m pytest tests/ -v" in makefile
    assert "$(PYTHON_BIN) -m black api/ ingestion/ tests/" in makefile
    assert "$(PYTHON_BIN) -m flake8 api/ ingestion/ tests/ --max-line-length=100" in makefile
    assert "ORDER_ID ?= ORD88888" in makefile
    assert "BUSINESS_SMOKE_AUDIT_FILE ?= /tmp/business_tool_audit.jsonl" in makefile
    assert "BUSINESS_SMOKE_FAKE_HTTP ?=" in makefile
    assert "RISK_RESPONSE_FILE ?=" in makefile
    assert "PROFIT_RESPONSE_FILE ?=" in makefile
    assert "BUSINESS_SAMPLE_VALIDATION_OUTPUT_FILE ?=" in makefile
    assert "BUSINESS_SMOKE_OUTPUT_FILE ?=" in makefile
    assert "BUSINESS_SMOKE_SUMMARY_ONLY ?=" in makefile
    assert "BUSINESS_CONTRACT_OUTPUT_FILE ?= /tmp/business_tool_contracts.json" in makefile
    assert "BUSINESS_CONTRACT_COMPACT ?=" in makefile
    assert "BUSINESS_ACCEPTANCE_PACK_OUTPUT_FILE ?= /tmp/business_tool_acceptance_pack.json" in makefile
    assert "BUSINESS_ACCEPTANCE_PACK_OPTIONAL_ARGS" in makefile
    assert "business-acceptance-pack:" in makefile
    assert "$(PYTHON_BIN) -B scripts/business_tool_acceptance_pack.py" in makefile
    assert "--output \"$(BUSINESS_ACCEPTANCE_PACK_OUTPUT_FILE)\"" in makefile
    assert "business-validate-samples:" in makefile
    assert "$(PYTHON_BIN) -B scripts/validate_business_response_samples.py" in makefile
    assert "examples/business_tool_samples/risk_response.sample.json" in makefile
    assert "examples/business_tool_samples/profit_response.sample.json" in makefile
    assert "--output \"$(BUSINESS_SAMPLE_VALIDATION_OUTPUT_FILE)\"" in makefile
    assert "business-contracts:" in makefile
    assert "$(PYTHON_BIN) -B scripts/export_business_contracts.py" in makefile
    assert "--output \"$(BUSINESS_CONTRACT_OUTPUT_FILE)\"" in makefile
    assert "$(if $(BUSINESS_CONTRACT_COMPACT),--compact,)" in makefile
    assert "$(PYTHON_BIN) -B scripts/business_tool_smoke.py" in makefile
    assert "--fake-http" in makefile
    assert "business-smoke-strict" in makefile
    assert "--fail-on-blocked" in makefile
    assert "--require-ready" in makefile
    assert "--output-file \"$(BUSINESS_SMOKE_OUTPUT_FILE)\"" in makefile
    assert "--summary-only" in makefile
    assert "--risk-response-file \"$(RISK_RESPONSE_FILE)\"" in makefile
    assert "--profit-response-file \"$(PROFIT_RESPONSE_FILE)\"" in makefile
    assert "BUSINESS_LLM_ACCEPTANCE_OUTPUT_FILE ?=" in makefile
    assert "BUSINESS_LLM_LOW_CONFIDENCE_THRESHOLD ?= 0.99" in makefile
    assert "$(PYTHON_BIN) -B scripts/business_tool_llm_acceptance.py" in makefile
    assert "--low-confidence-threshold \"$(BUSINESS_LLM_LOW_CONFIDENCE_THRESHOLD)\"" in makefile

    for source in (readme, doc):
        assert "make business-contracts" in source
        assert "BUSINESS_CONTRACT_OUTPUT_FILE=/tmp/business_tool_contracts.json" in source
        assert "make business-acceptance-pack" in source
        assert "BUSINESS_ACCEPTANCE_PACK_OUTPUT_FILE=/tmp/business_tool_acceptance_pack.json" in source
        assert "make business-smoke" in source
        assert "ORDER_ID=ORD88888" in source
        assert "BUSINESS_SMOKE_AUDIT_FILE=/tmp/business_tool_audit.jsonl" in source
        assert "BUSINESS_SMOKE_FAKE_HTTP=1" in source
        assert "RISK_RESPONSE_FILE=/tmp/risk_response.json" in source
        assert "PROFIT_RESPONSE_FILE=/tmp/profit_response.json" in source
        assert "readiness_check.overall_status" in source
        assert "--fail-on-blocked" in source
        assert "business-smoke-strict" in source
        assert "--require-ready" in source
        assert "--output-file" in source
        assert "--summary-only" in source
        assert "BUSINESS_SMOKE_OUTPUT_FILE=/tmp/business_smoke_report.json" in source
        assert "BUSINESS_SMOKE_SUMMARY_ONLY=1" in source
        assert "make business-validate-samples" in source
        assert "BUSINESS_SAMPLE_VALIDATION_OUTPUT_FILE=/tmp/business_sample_validation" in source
        assert "examples/business_tool_samples/risk_response.sample.json" in source
        assert "examples/business_tool_samples/profit_response.sample.json" in source
        assert "非 0" in source or "non-zero" in source
        assert "ready_with_warnings" in source

    assert "scripts/validate_business_response_samples.py" in doc
    for source in (readme, doc, quickstart_doc):
        assert "make business-validate-samples" in source
        assert "不回显完整" in source or (
            "never echoes" in source and "payload" in source
        )

    for source in (readme, doc, acceptance_doc):
        assert "make business-llm-acceptance" in source
        assert "BUSINESS_LLM_ACCEPTANCE_OUTPUT_FILE=/tmp/business_llm_acceptance.json" in source
        assert "selection_source=llm" in source

    for source in (readme, doc, acceptance_doc):
        assert "intent_precheck" in source

    for source in (readme, doc, acceptance_doc):
        assert "business_tool_acceptance_pack.json" in source
        assert "recommended_next_actions" in source


def test_business_response_sample_files_validate_without_exposing_payload_values():
    report = validate_response_samples(
        risk_response_file=str(RISK_SAMPLE_FILE),
        profit_response_file=str(PROFIT_SAMPLE_FILE),
    )

    assert report["status"] == "valid"
    assert report["validated_samples"] == ["profit", "risk"]
    assert report["invalid_samples"] == []
    assert report["results"]["risk"]["status"] == "valid"
    assert report["results"]["profit"]["status"] == "valid"
    assert "recommended_action" in report["results"]["risk"]["exposed_result_keys"]
    assert "platform_net_profit" in report["results"]["profit"]["exposed_result_keys"]

    report_text = json.dumps(report, ensure_ascii=False)
    assert "ORD88888" not in report_text
    assert "ORD12345" not in report_text
    assert "128.6" not in report_text
    assert "680.0" not in report_text


def test_business_response_sample_cli_reports_safe_missing_fields(tmp_path):
    invalid_profit_file = tmp_path / "profit-response-invalid.json"
    output_file = tmp_path / "sample-validation.json"
    invalid_profit_file.write_text(
        json.dumps(
            {
                "order_id": "ORD88888",
                "gross_amount": 128.6,
                "platform_commission": 19.29,
                "driver_income": 92.35,
                "subsidy": 8.0,
                "coupon": 6.0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/validate_business_response_samples.py",
            "--risk-response-file",
            str(RISK_SAMPLE_FILE),
            "--profit-response-file",
            str(invalid_profit_file),
            "--output",
            str(output_file),
        ],
        check=False,
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert "Wrote business response sample validation" in completed.stderr
    report = json.loads(output_file.read_text(encoding="utf-8"))
    assert report["status"] == "invalid"
    assert report["invalid_samples"] == ["profit"]
    assert report["results"]["profit"] == {
        "file": str(invalid_profit_file),
        "tool": "get_profit_chain_detail",
        "status": "invalid",
        "error_type": "BusinessContractError",
        "diagnostic_code": "missing_required_fields",
        "missing_fields": ["platform_net_profit"],
        "invalid_fields": [],
        "exposed_result_keys": [],
        "ignored_result_keys": [],
    }
    assert report["results"]["risk"]["status"] == "valid"

    report_text = json.dumps(report, ensure_ascii=False)
    assert "ORD88888" not in report_text
    assert "ORD12345" not in report_text
    assert "128.6" not in report_text
    assert "680.0" not in report_text


def test_business_acceptance_pack_combines_contracts_readiness_and_handoff(tmp_path):
    audit_file = tmp_path / "business-tool-audit.jsonl"

    pack = build_acceptance_pack(order_id="ORD88888", audit_file=str(audit_file))

    assert pack["status"] == "needs_attention"
    assert "contract_snapshot" in pack["acceptance_scope"]
    assert "readiness_gates" in pack["acceptance_scope"]
    assert "prompt_contract" in pack["acceptance_scope"]
    assert pack["contracts"]["risk"]["tool_name"] == "get_risk_event_detail"
    assert pack["contracts"]["profit"]["tool_name"] == "get_profit_chain_detail"
    assert pack["prompt_contract"]["profit"]["answer_perspectives"]["finance"]["label"] == "财务口径"
    assert pack["prompt_contract"]["risk_rule"]["answer_perspectives"]["strategy"]["label"] == "风控策略口径"
    assert any(
        "ignored_result_keys" in rule
        for rule in pack["prompt_contract"]["profit"]["safety_contract"]
    )
    assert pack["readiness_summary"]["overall_status"] == "ready_with_warnings"
    assert "readiness_items" in pack
    assert "captured_sample_validation" in pack["readiness_summary"]["warnings"]
    assert "external_http_configured" in pack["readiness_summary"]["warnings"]
    assert pack["safe_smoke_evidence"]["audit"]["file_configured"] is True
    assert pack["safe_smoke_evidence"]["query_smoke"]["execution_path"] == "inspected_intent"
    assert "ORD88888" not in json.dumps(
        pack["integration_handoff"], ensure_ascii=False
    )
    assert pack["integration_handoff"]["go_live_allowed"] is False
    assert "captured_sample_validation" in pack["integration_handoff"][
        "should_fix_before_production"
    ]
    assert any(
        "RISK_RESPONSE_FILE / PROFIT_RESPONSE_FILE" in action
        for action in pack["integration_handoff"]["recommended_next_actions"]
    )
    assert any(
        "外部真实风控/毛利 Base URL" in action
        for action in pack["integration_handoff"]["recommended_next_actions"]
    )
    assert pack["sample_handoff"] == {
        "templates": {
            "risk": "examples/business_tool_samples/risk_response.sample.json",
            "profit": "examples/business_tool_samples/profit_response.sample.json",
        },
        "default_validation_command": "make business-validate-samples",
        "custom_validation_command": (
            "make business-validate-samples "
            "RISK_RESPONSE_FILE=/tmp/risk_response.json "
            "PROFIT_RESPONSE_FILE=/tmp/profit_response.json "
            "BUSINESS_SAMPLE_VALIDATION_OUTPUT_FILE=/tmp/business_sample_validation.json"
        ),
        "report_safety": (
            "Only validation status, diagnostic codes, missing/invalid fields, "
            "and exposed result keys are returned; raw payload values are not echoed."
        ),
    }
    assert pack["source_commands"]["acceptance_pack"] == "make business-acceptance-pack"
    assert pack["source_commands"]["fake_http_acceptance_pack"] == (
        "make business-acceptance-pack BUSINESS_SMOKE_FAKE_HTTP=1"
    )
    assert pack["source_commands"]["sample_validation"] == "make business-validate-samples"
    assert "ORD88888" not in json.dumps(pack["sample_handoff"], ensure_ascii=False)


def test_business_acceptance_pack_writes_blocked_pack_when_smoke_fails(monkeypatch):
    def fail_smoke(**kwargs):
        raise ConnectionError("secret host detail must stay out")

    monkeypatch.setattr(business_tool_acceptance_pack, "run_smoke", fail_smoke)

    pack = build_acceptance_pack(order_id="ORD88888")

    assert pack["status"] == "blocked"
    assert pack["contracts"]["risk"]["tool_name"] == "get_risk_event_detail"
    assert "prompt_contract" in pack["acceptance_scope"]
    assert pack["prompt_contract"]["profit"]["name"] == "毛利抽成"
    assert pack["readiness_summary"]["overall_status"] == "blocked"
    assert pack["readiness_summary"]["blockers"] == ["smoke_execution"]
    assert pack["readiness_items"][0]["evidence"] == {
        "error_type": "ConnectionError",
        "diagnostic_code": "smoke_execution_failed",
    }
    assert pack["safe_smoke_evidence"] == {
        "smoke_execution": {
            "error_type": "ConnectionError",
            "diagnostic_code": "smoke_execution_failed",
        }
    }
    assert pack["sample_handoff"]["default_validation_command"] == (
        "make business-validate-samples"
    )
    assert pack["source_commands"]["sample_validation"] == "make business-validate-samples"
    assert "secret host detail" not in json.dumps(pack, ensure_ascii=False)
    assert any(
        "make business-smoke" in action
        for action in pack["integration_handoff"]["recommended_next_actions"]
    )


def test_business_acceptance_pack_reports_safe_profit_query_smoke_failure(monkeypatch):
    def fail_smoke(**kwargs):
        raise AssertionError("Profit query tool call failed: ConnectionError")

    monkeypatch.setattr(business_tool_acceptance_pack, "run_smoke", fail_smoke)

    pack = build_acceptance_pack(order_id="ORD88888")

    assert pack["status"] == "blocked"
    evidence = pack["safe_smoke_evidence"]["smoke_execution"]
    assert evidence == {
        "error_type": "AssertionError",
        "diagnostic_code": "profit_query_tool_call_failed",
        "tool": "get_profit_chain_detail",
        "safe_failure_type": "ConnectionError",
        "suggested_action": (
            "检查 PROFIT_API_BASE_URL / PROFIT_API_KEY，或使用 "
            "BUSINESS_SMOKE_FAKE_HTTP=1 验证本地 HTTP 合同链路。"
        ),
    }
    assert pack["readiness_items"][0]["evidence"] == evidence
    encoded = json.dumps(pack, ensure_ascii=False)
    assert "Profit query tool call failed" not in encoded
    assert "ORD88888" not in json.dumps(pack["sample_handoff"], ensure_ascii=False)


def test_business_tool_smoke_cli_writes_full_report_and_prints_summary(tmp_path):
    output_file = tmp_path / "business-smoke-report.json"
    audit_file = tmp_path / "business-tool-audit.jsonl"

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/business_tool_smoke.py",
            "--order-id",
            "ORD88888",
            "--audit-file",
            str(audit_file),
            "--summary-only",
            "--output-file",
            str(output_file),
        ],
        check=False,
        cwd=Path.cwd(),
        env=smoke_cli_env(),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert '"overall_status": "ready_with_warnings"' in completed.stdout
    assert '"warning_count": 4' in completed.stdout
    assert '"external_http_configured"' in completed.stdout
    assert '"items"' not in completed.stdout
    assert '"runtime_failure_smoke"' not in completed.stdout
    assert "ORD88888" not in completed.stdout

    report = json.loads(output_file.read_text(encoding="utf-8"))
    assert report["status"] == "ok"
    assert report["order_id"] == "ORD88888"
    assert report["readiness_check"]["overall_status"] == "ready_with_warnings"
    assert "items" in report["readiness_check"]
    assert report["runtime_failure_smoke"]["status"] == "error"
    assert report["audit"]["file"] == str(audit_file)


def test_business_tool_smoke_cli_fails_when_readiness_is_blocked(tmp_path):
    profit_response_file = tmp_path / "profit-response.json"
    profit_response_file.write_text(
        json.dumps(
            {
                "order_id": "ORD88888",
                "gross_amount": 128.6,
                "platform_commission": 19.29,
                "driver_income": 92.35,
                "subsidy": 8.0,
                "coupon": 6.0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/business_tool_smoke.py",
            "--order-id",
            "ORD88888",
            "--profit-response-file",
            str(profit_response_file),
            "--fail-on-blocked",
        ],
        check=False,
        cwd=Path.cwd(),
        env=smoke_cli_env(),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert '"overall_status": "blocked"' in completed.stdout
    assert '"captured_sample_validation"' in completed.stdout
    assert "ORD88888" not in completed.stdout.split('"readiness_check":', 1)[1]
    assert "128.6" not in completed.stdout.split('"readiness_check":', 1)[1]


def test_business_tool_smoke_cli_require_ready_fails_on_warnings(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/business_tool_smoke.py",
            "--order-id",
            "ORD88888",
            "--audit-file",
            str(tmp_path / "business-tool-audit.jsonl"),
            "--require-ready",
        ],
        check=False,
        cwd=Path.cwd(),
        env=smoke_cli_env(),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 3
    assert '"overall_status": "ready_with_warnings"' in completed.stdout
    assert '"real_http_configured"' in completed.stdout
    assert '"access_control_enabled"' in completed.stdout
    assert "ORD88888" not in completed.stdout.split('"readiness_check":', 1)[1]


def test_business_tool_smoke_checks_mock_contracts_and_safe_audit_file(tmp_path):
    audit_file = tmp_path / "business-tool-audit.jsonl"
    risk_response_file = tmp_path / "risk-response.json"
    profit_response_file = tmp_path / "profit-response.json"
    risk_response_file.write_text(
        json.dumps(
            {
                "order_id": "ORD88888",
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
                "operator_phone": "13900001111",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    profit_response_file.write_text(
        json.dumps(
            {
                "order_id": "ORD88888",
                "gross_amount": 128.6,
                "platform_commission": 19.29,
                "driver_income": 92.35,
                "subsidy": 8.0,
                "coupon": 6.0,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = run_smoke(
        order_id="ORD88888",
        audit_file=str(audit_file),
        risk_response_file=str(risk_response_file),
        profit_response_file=str(profit_response_file),
    )

    assert report["status"] == "ok"
    assert report["contracts"]["risk_tool"] == "get_risk_event_detail"
    assert report["contracts"]["profit_tool"] == "get_profit_chain_detail"
    assert report["runtime_status"]["status"] in {"ready", "disabled", "misconfigured"}
    assert report["runtime_status"]["business_tools"]["enabled"] is True
    assert report["runtime_status"]["business_tools"]["tool_count"] == 2
    assert report["runtime_status"]["access_control"]["enabled"] is False
    assert report["runtime_status"]["access_control"]["ready"] is True
    assert report["runtime_status"]["llm_intent"]["enabled"] is False
    assert {
        tool["tool_name"]: tool["data_source"]
        for tool in report["runtime_status"]["tools"]
    } == {
        "get_risk_event_detail": "mock",
        "get_profit_chain_detail": "mock",
    }
    assert {
        tool["tool_name"]: tool["integration_mode"]
        for tool in report["runtime_status"]["tools"]
    } == {
        "get_risk_event_detail": "mock",
        "get_profit_chain_detail": "mock",
    }
    assert all(
        isinstance(tool["base_url_configured"], bool)
        and isinstance(tool["api_key_configured"], bool)
        for tool in report["runtime_status"]["tools"]
    )
    runtime_status_text = json.dumps(report["runtime_status"], ensure_ascii=False)
    assert "https://" not in runtime_status_text
    assert "Bearer " not in runtime_status_text
    assert report["probes"]["risk"]["status"] == "success"
    assert report["probes"]["profit"]["status"] == "success"
    assert report["probes"]["risk"]["audit_id"].startswith("bt-")
    assert report["probes"]["profit"]["audit_id"].startswith("bt-")
    assert report["intent_precheck_smoke"] == {
        "checks": [
            {
                "scene_type": "risk_rule",
                "expected_tool_name": "get_risk_event_detail",
                "tool_name": "get_risk_event_detail",
                "selection_source": "rules",
                "confidence": 0.92,
                "missing_fields": [],
                "needs_clarification": False,
                "selected_expected_tool": True,
            },
            {
                "scene_type": "profit",
                "expected_tool_name": "get_profit_chain_detail",
                "tool_name": "get_profit_chain_detail",
                "selection_source": "rules",
                "confidence": 0.92,
                "missing_fields": [],
                "needs_clarification": False,
                "selected_expected_tool": True,
            },
        ],
        "selected_expected_count": 2,
        "needs_clarification_count": 0,
    }
    intent_precheck_text = json.dumps(report["intent_precheck_smoke"], ensure_ascii=False)
    assert "ORD12345" not in intent_precheck_text
    assert "ORD88888" not in intent_precheck_text
    assert report["query_smoke"]["intent"]["tool_name"] == "get_profit_chain_detail"
    assert report["query_smoke"]["intent"]["order_id"] == "ORD88888"
    assert report["query_smoke"]["intent"]["needs_clarification"] is False
    assert report["query_smoke"]["execution_path"] == "inspected_intent"
    assert report["query_smoke"]["tool_call"]["status"] == "success"
    assert report["query_smoke"]["tool_call"]["audit_id"].startswith("bt-")
    assert report["query_smoke"]["tool_context_checks"] == {
        "has_endpoint_path": True,
        "has_profit_fields": True,
    }
    assert report["contract_failure_smoke"] == {
        "tool": "get_profit_chain_detail",
        "status": "invalid",
        "error_type": "BusinessContractError",
        "diagnostic_code": "missing_required_fields",
        "missing_fields": ["platform_net_profit"],
        "invalid_fields": [],
        "payload_values_exposed": False,
    }
    assert report["runtime_failure_smoke"]["tool"] == "get_profit_chain_detail"
    assert report["runtime_failure_smoke"]["status"] == "error"
    assert report["runtime_failure_smoke"]["error_type"] == "RuntimeError"
    assert report["runtime_failure_smoke"]["audit_id"].startswith("bt-")
    assert report["runtime_failure_smoke"]["has_empty_result"] is True
    assert report["runtime_failure_smoke"]["summary_is_safe"] is True
    assert report["runtime_failure_smoke"]["tool_context_checks"] == {
        "has_error_type": True,
        "raw_error_exposed": False,
    }
    assert report["runtime_failure_smoke"]["audit_checks"] == {
        "status": "error",
        "error_type": "RuntimeError",
        "raw_error_exposed": False,
    }
    assert "database password leaked" not in json.dumps(
        report["runtime_failure_smoke"],
        ensure_ascii=False,
    )
    assert report["unsafe_order_id_smoke"] == {
        "probe_status": "rejected",
        "probe_error": "order_id contains unsupported characters",
        "llm_intent": {
            "tool_name": "get_profit_chain_detail",
            "order_id": None,
            "missing_fields": ["order_id"],
            "needs_clarification": True,
        },
        "tool_call_count": 0,
        "unsafe_value_exposed": False,
    }
    assert "../admin" not in json.dumps(report["unsafe_order_id_smoke"], ensure_ascii=False)
    assert "secret" not in json.dumps(report["unsafe_order_id_smoke"], ensure_ascii=False)
    assert report["http_transport_failure_smoke"] == {
        "http_401": {
            "status": "error",
            "error_type": "ConnectionError",
            "safe_message": "Business API HTTP error: status=401",
            "raw_details_exposed": False,
        },
        "http_500": {
            "status": "error",
            "error_type": "ConnectionError",
            "safe_message": "Business API HTTP error: status=500",
            "raw_details_exposed": False,
        },
        "url_error": {
            "status": "error",
            "error_type": "ConnectionError",
            "safe_message": "Business API connection failed",
            "raw_details_exposed": False,
        },
        "timeout": {
            "status": "error",
            "error_type": "TimeoutError",
            "safe_message": "Business API request timed out",
            "raw_details_exposed": False,
        },
    }
    transport_report_text = json.dumps(
        report["http_transport_failure_smoke"],
        ensure_ascii=False,
    )
    assert "transport-secret" not in transport_report_text
    assert "profit.example.test" not in transport_report_text
    assert "ORD88888" not in transport_report_text
    assert "Unauthorized" not in transport_report_text
    assert report["sample_validations"]["risk"]["status"] == "valid"
    assert report["sample_validations"]["risk"]["diagnostic_code"] is None
    assert "recommended_action" in report["sample_validations"]["risk"]["exposed_result_keys"]
    assert report["sample_validations"]["risk"]["ignored_result_keys"] == ["operator_phone"]
    assert report["sample_validations"]["risk"]["payload_values_exposed"] is False
    assert report["sample_validations"]["profit"] == {
        "file": str(profit_response_file),
        "tool": "get_profit_chain_detail",
        "status": "invalid",
        "error_type": "BusinessContractError",
        "diagnostic_code": "missing_required_fields",
        "missing_fields": ["platform_net_profit"],
        "invalid_fields": [],
        "exposed_result_keys": [],
        "ignored_result_keys": [],
        "payload_values_exposed": False,
    }
    assert "ORD88888" not in json.dumps(report["sample_validations"], ensure_ascii=False)
    assert "128.6" not in json.dumps(report["sample_validations"], ensure_ascii=False)
    assert report["readiness_check"]["overall_status"] == "blocked"
    assert "captured_sample_validation" in report["readiness_check"]["blockers"]
    assert "real_http_configured" in report["readiness_check"]["warnings"]
    assert "external_http_configured" in report["readiness_check"]["warnings"]
    assert "access_control_enabled" in report["readiness_check"]["warnings"]
    assert "persistent_audit_enabled" not in report["readiness_check"]["warnings"]
    assert "business_tools_enabled" in report["readiness_check"]["passed"]
    assert "intent_precheck" in report["readiness_check"]["passed"]
    assert "natural_language_tool_selection" in report["readiness_check"]["passed"]
    assert "audit_traceability" in report["readiness_check"]["passed"]
    assert "probe_endpoints" in report["readiness_check"]["passed"]
    assert "safe_runtime_degradation" in report["readiness_check"]["passed"]
    readiness_text = json.dumps(report["readiness_check"], ensure_ascii=False)
    assert "ORD88888" not in readiness_text
    assert "128.6" not in readiness_text
    assert "13900001111" not in readiness_text
    assert "transport-secret" not in readiness_text
    assert "profit.example.test" not in readiness_text
    intent_item = next(
        item for item in report["readiness_check"]["items"] if item["id"] == "intent_precheck"
    )
    assert intent_item["status"] == "passed"
    assert intent_item["evidence"] == {"checks": report["intent_precheck_smoke"]["checks"]}
    assert report["audit"]["event_count"] == 4
    sample_item = next(
        item
        for item in report["readiness_check"]["items"]
        if item["id"] == "captured_sample_validation"
    )
    assert sample_item["status"] == "blocked"
    assert sample_item["evidence"]["ignored_result_keys"] == {
        "risk": ["operator_phone"]
    }
    assert sample_item["evidence"]["invalid_samples"]["profit"] == {
        "status": "invalid",
        "diagnostic_code": "missing_required_fields",
        "missing_fields": ["platform_net_profit"],
        "invalid_fields": [],
    }


def test_business_tool_smoke_fake_http_mode_passes_real_http_configuration(tmp_path):
    audit_file = tmp_path / "business-tool-audit.jsonl"
    original_http_runtime = run_smoke.__globals__["_fake_http_runtime"]

    class FakeContextManager:
        def __enter__(self):
            from api.config import settings

            settings.risk_api_base_url = "http://127.0.0.1:8000/api/v1/business-tools/fake-http"
            settings.risk_api_key = "fake-risk-token"
            settings.profit_api_base_url = "http://127.0.0.1:8000/api/v1/business-tools/fake-http"
            settings.profit_api_key = "fake-profit-token"
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_http_runtime(*, order_id):
        return FakeContextManager()

    def fake_urlopen(req, timeout):
        path = req.full_url.replace("http://127.0.0.1:8000/api/v1/business-tools/fake-http", "")
        if path == "/risk/events/ORD88888":
            payload = fake_risk_payload("ORD88888")
        elif path == "/profit/orders/ORD88888/chain":
            payload = fake_profit_payload("ORD88888")
        else:
            raise AssertionError(f"unexpected fake-http path: {path}")

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return body

        return FakeResponse()

    run_smoke.__globals__["_fake_http_runtime"] = fake_http_runtime
    from api.services import business_clients

    original_urlopen = business_clients.request.urlopen
    business_clients.request.urlopen = fake_urlopen
    try:
        report = run_smoke(
            order_id="ORD88888",
            audit_file=str(audit_file),
            use_fake_http=True,
        )
    finally:
        run_smoke.__globals__["_fake_http_runtime"] = original_http_runtime
        business_clients.request.urlopen = original_urlopen

    assert report["status"] == "ok"
    assert report["fake_http"] is True
    assert {
        tool["tool_name"]: tool["data_source"]
        for tool in report["runtime_status"]["tools"]
    } == {
        "get_risk_event_detail": "http",
        "get_profit_chain_detail": "http",
    }
    assert {
        tool["tool_name"]: tool["integration_mode"]
        for tool in report["runtime_status"]["tools"]
    } == {
        "get_risk_event_detail": "fake_http",
        "get_profit_chain_detail": "fake_http",
    }
    assert all(
        tool["base_url_configured"] is True and tool["api_key_configured"] is True
        for tool in report["runtime_status"]["tools"]
    )
    assert report["probes"]["risk"]["data_source"] == "http"
    assert report["probes"]["profit"]["data_source"] == "http"
    assert "real_http_configured" in report["readiness_check"]["passed"]
    assert "real_http_configured" not in report["readiness_check"]["warnings"]
    assert "external_http_configured" in report["readiness_check"]["warnings"]
    real_http_item = next(
        item
        for item in report["readiness_check"]["items"]
        if item["id"] == "real_http_configured"
    )
    assert "进程内 fake HTTP transport" in real_http_item["summary"]
    assert "外部真实 HTTP 接口" not in real_http_item["summary"]
    assert real_http_item["evidence"]["fake_http"] is True
    assert real_http_item["evidence"]["integration_modes"] == ["fake_http"]
    assert {
        tool["tool_name"]: tool["integration_mode"]
        for tool in real_http_item["evidence"]["tool_sources"]
    } == {
        "get_risk_event_detail": "fake_http",
        "get_profit_chain_detail": "fake_http",
    }
    external_http_item = next(
        item
        for item in report["readiness_check"]["items"]
        if item["id"] == "external_http_configured"
    )
    assert external_http_item["status"] == "warning"
    assert external_http_item["evidence"]["external_http_ready"] is False
    assert external_http_item["evidence"]["integration_modes"] == ["fake_http"]
    assert report["readiness_check"]["overall_status"] == "ready_with_warnings"
    readiness_text = json.dumps(report["readiness_check"], ensure_ascii=False)
    assert "http://127.0.0.1" not in readiness_text
    assert "fake-risk-token" not in readiness_text
    assert "fake-profit-token" not in readiness_text
    assert report["audit"]["event_count"] >= 4
    assert report["audit"]["file"] == str(audit_file)

    content = audit_file.read_text(encoding="utf-8")
    assert "ORD88888" not in content
    assert "database password leaked" not in content
    events = [json.loads(line) for line in content.splitlines()]
    assert len(events) >= 4
    assert all(event["audit_id"].startswith("bt-") for event in events)
    assert all(event["arguments"]["order_id"] != "ORD88888" for event in events)
    assert any(
        event.get("selection_reason")
        and "ORD***888" in event["selection_reason"]
        and "ORD88888" not in event["selection_reason"]
        and isinstance(event.get("confidence"), (int, float))
        for event in events
    )
    audit_traceability_item = next(
        item
        for item in report["readiness_check"]["items"]
        if item["id"] == "audit_traceability"
    )
    assert audit_traceability_item["status"] == "passed"
    assert audit_traceability_item["evidence"] == {
        "audit_id": report["query_smoke"]["tool_call"]["audit_id"],
        "event_found": True,
        "has_selection_reason": True,
        "has_confidence": True,
    }


def test_business_tool_smoke_fake_http_minimum_contract_derives_chain_and_filters_sensitive_fields(
    tmp_path,
):
    audit_file = tmp_path / "business-tool-audit.jsonl"
    original_http_runtime = run_smoke.__globals__["_fake_http_runtime"]

    class FakeContextManager:
        def __enter__(self):
            from api.config import settings

            settings.risk_api_base_url = "http://127.0.0.1:8000/api/v1/business-tools/fake-http"
            settings.risk_api_key = "fake-risk-token"
            settings.profit_api_base_url = "http://127.0.0.1:8000/api/v1/business-tools/fake-http"
            settings.profit_api_key = "fake-profit-token"
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_http_runtime(*, order_id):
        return FakeContextManager()

    def fake_urlopen(req, timeout):
        path = req.full_url.replace("http://127.0.0.1:8000/api/v1/business-tools/fake-http", "")
        if path == "/risk/events/ORD88888":
            payload = {
                "order_id": "ORD88888",
                "decision": "review",
                "risk_score": 68,
                "hit_rules": [
                    {
                        "rule_id": "RISK-mid-007",
                        "rule_name": "设备与支付行为需复核",
                        "evidence": "设备与支付信息组合命中复核规则",
                        "internal_case_id": "case-secret",
                    }
                ],
                "recommended_action": "建议复核。",
                "operator_note": "仅内部可见",
            }
        elif path == "/profit/orders/ORD88888/chain":
            payload = {
                "order_id": "ORD88888",
                "gross_amount": 128.6,
                "platform_commission": 19.29,
                "driver_income": 92.35,
                "subsidy": 8.0,
                "coupon": 6.0,
                "platform_net_profit": 5.29,
                "driver_phone": "13800000000",
                "internal_settlement_id": "settlement-secret",
                "driver_income_detail": {
                    "base_fare": 70.0,
                    "distance_fee": 22.35,
                    "driver_id_card": "hidden-id-card",
                },
            }
        else:
            raise AssertionError(f"unexpected fake-http path: {path}")

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return body

        return FakeResponse()

    run_smoke.__globals__["_fake_http_runtime"] = fake_http_runtime
    from api.services import business_clients

    original_urlopen = business_clients.request.urlopen
    business_clients.request.urlopen = fake_urlopen
    try:
        report = run_smoke(
            order_id="ORD88888",
            audit_file=str(audit_file),
            use_fake_http=True,
        )
    finally:
        run_smoke.__globals__["_fake_http_runtime"] = original_http_runtime
        business_clients.request.urlopen = original_urlopen

    assert report["status"] == "ok"
    assert report["fake_http"] is True
    assert report["probes"]["profit"]["status"] == "success"
    assert report["query_smoke"]["tool_call"]["status"] == "success"
    assert report["probes"]["profit"]["result_keys"] == [
        "chain",
        "chain_source",
        "coupon",
        "driver_income",
        "driver_income_detail",
        "gross_amount",
        "order_id",
        "platform_commission",
        "platform_net_profit",
        "subsidy",
    ]
    assert report["query_smoke"]["tool_call"]["result_keys"] == [
        "chain",
        "chain_source",
        "coupon",
        "driver_income",
        "driver_income_detail",
        "gross_amount",
        "order_id",
        "platform_commission",
        "platform_net_profit",
        "subsidy",
    ]
    assert "real_http_configured" in report["readiness_check"]["passed"]
    assert "external_http_configured" in report["readiness_check"]["warnings"]
    assert report["readiness_check"]["overall_status"] == "ready_with_warnings"

    content = audit_file.read_text(encoding="utf-8")
    assert "13800000000" not in content
    assert "settlement-secret" not in content
    assert "hidden-id-card" not in content
    assert "case-secret" not in content
    assert "仅内部可见" not in content
    assert "ORD88888" not in content

    events = [json.loads(line) for line in content.splitlines()]
    profit_event = next(
        event for event in events if event["tool_name"] == "get_profit_chain_detail" and event["status"] == "success"
    )
    risk_event = next(
        event for event in events if event["tool_name"] == "get_risk_event_detail" and event["status"] == "success"
    )

    assert profit_event["result_keys"] == [
        "chain",
        "chain_source",
        "coupon",
        "driver_income",
        "driver_income_detail",
        "gross_amount",
        "order_id",
        "platform_commission",
        "platform_net_profit",
        "subsidy",
    ]
    assert "driver_phone" not in profit_event["result_keys"]
    assert "internal_settlement_id" not in profit_event["result_keys"]
    assert "operator_note" not in risk_event["result_keys"]

    readiness_text = json.dumps(report["readiness_check"], ensure_ascii=False)
    assert "13800000000" not in readiness_text
    assert "settlement-secret" not in readiness_text
    assert "hidden-id-card" not in readiness_text
    assert any(
        event["status"] == "error" and event["error_type"] == "RuntimeError"
        for event in events
    )
