"""
Business tool integration smoke check.

Run this before wiring real risk/profit systems into the assistant. It exercises
the natural-language tool selection path plus the same service boundary used by
the API probe endpoint, validates safe audit events, and prints a compact JSON
report.
"""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.config import settings
from api.services.business_contracts import (
    PROFIT_REQUIRED_FIELDS,
    PROFIT_TOOL_NAME,
    RISK_REQUIRED_FIELDS,
    RISK_TOOL_NAME,
    contract_snapshot,
    fake_profit_payload,
    fake_risk_payload,
    endpoint_path,
)
from api.services import business_clients
from api.services.business_clients import ProfitSystemClient, reset_business_clients
from api.services.tool_service import get_tool_service, reset_tool_service

RUNTIME_FAILURE_MESSAGE = "database password leaked in stack"
HTTP_TRANSPORT_SECRET = "transport-secret"
HTTP_TRANSPORT_HOST = "profit.example.test"
LOCAL_FAKE_HTTP_BASE_URL = "http://127.0.0.1:8000/api/v1/business-tools/fake-http"


def run_smoke(
    *,
    order_id: str,
    audit_file: Optional[str] = None,
    risk_response_file: Optional[str] = None,
    profit_response_file: Optional[str] = None,
    use_fake_http: bool = False,
) -> Dict[str, Any]:
    """Run a local risk/profit tool smoke check and return a safe report."""
    order_id = (order_id or "").strip()
    if not order_id:
        raise ValueError("order_id is required")

    previous_audit_enabled = settings.enable_business_tool_audit_file
    previous_audit_file = settings.business_tool_audit_file
    previous_risk_base_url = settings.risk_api_base_url
    previous_risk_api_key = settings.risk_api_key
    previous_profit_base_url = settings.profit_api_base_url
    previous_profit_api_key = settings.profit_api_key

    try:
        http_context = _fake_http_runtime(order_id=order_id) if use_fake_http else nullcontext()
        with http_context:
            if audit_file:
                settings.enable_business_tool_audit_file = True
                settings.business_tool_audit_file = audit_file

            reset_business_clients()
            reset_tool_service()
            service = get_tool_service()

            contracts = contract_snapshot()
            runtime_status = _runtime_status_summary(service.runtime_status())
            intent_precheck_smoke = _run_intent_precheck_smoke(service=service)
            profit_query = f"查询订单 {order_id} 的抽成和司机收入"
            profit_query_smoke = _run_profit_query_smoke(
                service=service,
                query=profit_query,
                order_id=order_id,
            )
            contract_failure_smoke = _run_contract_failure_smoke(
                service=service,
                order_id=order_id,
            )
            runtime_failure_smoke = _run_runtime_failure_smoke(
                service=service,
                query=profit_query,
            )
            unsafe_order_id_smoke = _run_unsafe_order_id_smoke(service=service)
            http_transport_failure_smoke = _run_http_transport_failure_smoke(
                order_id=order_id,
            )
            sample_validations = _run_sample_file_validations(
                service=service,
                risk_response_file=risk_response_file,
                profit_response_file=profit_response_file,
            )
            risk_probe = service.probe(tool_name=RISK_TOOL_NAME, order_id=order_id)
            profit_probe = service.probe(tool_name=PROFIT_TOOL_NAME, order_id=order_id)
            _assert_probe_success("risk", risk_probe, RISK_REQUIRED_FIELDS)
            _assert_probe_success("profit", profit_probe, PROFIT_REQUIRED_FIELDS)

            events = service.list_audit_events(limit=10)
            _assert_safe_audit_events(events=events, order_id=order_id, expected_count=4)
            if audit_file:
                _assert_audit_file_safe(
                    audit_file=audit_file,
                    order_id=order_id,
                    forbidden_texts=[RUNTIME_FAILURE_MESSAGE],
                )

            readiness_check = _build_readiness_check(
                runtime_status=runtime_status,
                probes={"risk": risk_probe, "profit": profit_probe},
                intent_precheck_smoke=intent_precheck_smoke,
                query_smoke=profit_query_smoke,
                contract_failure_smoke=contract_failure_smoke,
                runtime_failure_smoke=runtime_failure_smoke,
                unsafe_order_id_smoke=unsafe_order_id_smoke,
                http_transport_failure_smoke=http_transport_failure_smoke,
                sample_validations=sample_validations,
                audit_events=events,
                audit_file=audit_file,
            )

            return {
                "status": "ok",
                "order_id": order_id,
                "contracts": {
                    "risk_tool": contracts["risk"]["tool_name"],
                    "profit_tool": contracts["profit"]["tool_name"],
                    "risk_endpoint": contracts["risk"]["endpoint_template"],
                    "profit_endpoint": contracts["profit"]["endpoint_template"],
                },
                "runtime_status": runtime_status,
                "probes": {
                    "risk": _probe_summary(risk_probe),
                    "profit": _probe_summary(profit_probe),
                },
                "intent_precheck_smoke": intent_precheck_smoke,
                "query_smoke": profit_query_smoke,
                "contract_failure_smoke": contract_failure_smoke,
                "runtime_failure_smoke": runtime_failure_smoke,
                "unsafe_order_id_smoke": unsafe_order_id_smoke,
                "http_transport_failure_smoke": http_transport_failure_smoke,
                "sample_validations": sample_validations,
                "readiness_check": readiness_check,
                "audit": {
                    "event_count": len(events),
                    "audit_ids": [event["audit_id"] for event in events[:4]],
                    "file": audit_file or None,
                },
                "fake_http": use_fake_http,
            }
    finally:
        settings.enable_business_tool_audit_file = previous_audit_enabled
        settings.business_tool_audit_file = previous_audit_file
        settings.risk_api_base_url = previous_risk_base_url
        settings.risk_api_key = previous_risk_api_key
        settings.profit_api_base_url = previous_profit_base_url
        settings.profit_api_key = previous_profit_api_key
        reset_business_clients()
        reset_tool_service()


def _fake_http_runtime(*, order_id: str):
    previous_urlopen = business_clients.request.urlopen

    def fake_urlopen(req, timeout):
        del timeout
        full_url = getattr(req, "full_url", str(req))
        path = full_url.replace(LOCAL_FAKE_HTTP_BASE_URL, "", 1)
        if path == endpoint_path(RISK_TOOL_NAME, order_id=order_id):
            payload = fake_risk_payload(order_id)
        elif path == endpoint_path(PROFIT_TOOL_NAME, order_id=order_id):
            payload = fake_profit_payload(order_id)
        else:
            raise URLError("fake business endpoint not found")

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return body

        return FakeResponse()

    @contextmanager
    def fake_runtime():
        business_clients.request.urlopen = fake_urlopen
        try:
            yield
        finally:
            business_clients.request.urlopen = previous_urlopen

    settings.risk_api_base_url = LOCAL_FAKE_HTTP_BASE_URL
    settings.risk_api_key = "fake-risk-token"
    settings.profit_api_base_url = LOCAL_FAKE_HTTP_BASE_URL
    settings.profit_api_key = "fake-profit-token"
    return fake_runtime()


def _run_sample_file_validations(
    *,
    service: Any,
    risk_response_file: Optional[str],
    profit_response_file: Optional[str],
) -> Dict[str, Any]:
    """Validate optional captured real-system response samples from JSON files."""
    validations = {}
    if risk_response_file:
        validations["risk"] = _validate_response_file(
            service=service,
            tool_name=RISK_TOOL_NAME,
            path=risk_response_file,
        )
    if profit_response_file:
        validations["profit"] = _validate_response_file(
            service=service,
            tool_name=PROFIT_TOOL_NAME,
            path=profit_response_file,
        )
    return validations


def _run_intent_precheck_smoke(*, service: Any) -> Dict[str, Any]:
    """Verify standard risk/profit prompts can be routed without tool execution."""
    checks = service._intent_precheck_readiness_checks()
    safe_checks = [
        {
            "scene_type": check.get("scene_type"),
            "expected_tool_name": check.get("expected_tool_name"),
            "tool_name": check.get("tool_name"),
            "selection_source": check.get("selection_source"),
            "confidence": check.get("confidence"),
            "missing_fields": check.get("missing_fields") or [],
            "needs_clarification": bool(check.get("needs_clarification")),
            "selected_expected_tool": bool(check.get("selected_expected_tool")),
        }
        for check in checks
    ]
    return {
        "checks": safe_checks,
        "selected_expected_count": sum(
            1 for check in safe_checks if check["selected_expected_tool"]
        ),
        "needs_clarification_count": sum(
            1 for check in safe_checks if check["needs_clarification"]
        ),
    }


def _build_readiness_check(
    *,
    runtime_status: Dict[str, Any],
    probes: Dict[str, Dict[str, Any]],
    intent_precheck_smoke: Dict[str, Any],
    query_smoke: Dict[str, Any],
    contract_failure_smoke: Dict[str, Any],
    runtime_failure_smoke: Dict[str, Any],
    unsafe_order_id_smoke: Dict[str, Any],
    http_transport_failure_smoke: Dict[str, Any],
    sample_validations: Dict[str, Any],
    audit_events: list[Dict[str, Any]],
    audit_file: Optional[str],
) -> Dict[str, Any]:
    """Build a safe integration-readiness checklist from smoke evidence."""
    intent_checks = intent_precheck_smoke.get("checks") or []
    intent_precheck_passed = bool(intent_checks) and all(
        item.get("selected_expected_tool") and not item.get("needs_clarification")
        for item in intent_checks
    )
    items = [
        _readiness_item(
            check_id="business_tools_enabled",
            status="passed"
            if runtime_status.get("business_tools", {}).get("enabled")
            else "blocked",
            summary="业务工具开关已启用"
            if runtime_status.get("business_tools", {}).get("enabled")
            else "业务工具开关未启用",
            evidence={
                "tool_count": runtime_status.get("business_tools", {}).get("tool_count"),
                "timeout_seconds": runtime_status.get("business_tools", {}).get(
                    "timeout_seconds"
                ),
            },
        ),
        _readiness_item(
            check_id="tool_contracts_available",
            status="passed"
            if all(tool.get("contract_available") for tool in runtime_status.get("tools") or [])
            else "blocked",
            summary="风控/毛利工具合同可用",
            evidence={
                "tools": [
                    {
                        "tool_name": tool.get("tool_name"),
                        "contract_available": tool.get("contract_available"),
                    }
                    for tool in runtime_status.get("tools") or []
                ]
            },
        ),
        _readiness_item(
            check_id="intent_precheck",
            status="passed" if intent_precheck_passed else "blocked",
            summary=(
                "风控/毛利标准问题均可在不执行接口的情况下完成工具意图预检"
            )
            if intent_precheck_passed
            else "存在标准问题未能稳定预检到目标工具或仍需澄清",
            evidence={"checks": intent_checks},
        ),
        _readiness_item(
            check_id="natural_language_tool_selection",
            status="passed"
            if query_smoke.get("intent", {}).get("tool_name") == PROFIT_TOOL_NAME
            and query_smoke.get("tool_call", {}).get("status") == "success"
            and all(query_smoke.get("tool_context_checks", {}).values())
            else "blocked",
            summary="自然语言毛利问题可选择并执行订单毛利工具",
            evidence={
                "tool_name": query_smoke.get("intent", {}).get("tool_name"),
                "tool_status": query_smoke.get("tool_call", {}).get("status"),
                "tool_context_checks": query_smoke.get("tool_context_checks"),
            },
        ),
        _readiness_item(
            check_id="probe_endpoints",
            status="passed"
            if all(probe.get("status") == "success" for probe in probes.values())
            else "blocked",
            summary="风控和毛利探测均成功",
            evidence={
                name: {
                    "status": probe.get("status"),
                    "data_source": probe.get("data_source"),
                    "has_endpoint_path": bool(probe.get("endpoint_path")),
                }
                for name, probe in probes.items()
            },
        ),
        _audit_traceability_readiness_item(
            query_smoke=query_smoke,
            audit_events=audit_events,
        ),
        _readiness_item(
            check_id="safe_contract_diagnostics",
            status="passed"
            if contract_failure_smoke.get("status") == "invalid"
            and contract_failure_smoke.get("payload_values_exposed") is False
            else "blocked",
            summary="合同失败诊断结构化且不回显提交值",
            evidence={
                "diagnostic_code": contract_failure_smoke.get("diagnostic_code"),
                "payload_values_exposed": contract_failure_smoke.get(
                    "payload_values_exposed"
                ),
            },
        ),
        _readiness_item(
            check_id="safe_runtime_degradation",
            status="passed"
            if runtime_failure_smoke.get("status") == "error"
            and runtime_failure_smoke.get("has_empty_result")
            and runtime_failure_smoke.get("summary_is_safe")
            else "blocked",
            summary="运行异常会降级为安全错误卡片和空结果",
            evidence={
                "error_type": runtime_failure_smoke.get("error_type"),
                "has_empty_result": runtime_failure_smoke.get("has_empty_result"),
                "summary_is_safe": runtime_failure_smoke.get("summary_is_safe"),
            },
        ),
        _readiness_item(
            check_id="safe_order_id_handling",
            status="passed"
            if unsafe_order_id_smoke.get("probe_status") == "rejected"
            and unsafe_order_id_smoke.get("tool_call_count") == 0
            and unsafe_order_id_smoke.get("unsafe_value_exposed") is False
            else "blocked",
            summary="不安全订单号会被拒绝且不会执行工具",
            evidence={
                "probe_status": unsafe_order_id_smoke.get("probe_status"),
                "tool_call_count": unsafe_order_id_smoke.get("tool_call_count"),
                "unsafe_value_exposed": unsafe_order_id_smoke.get("unsafe_value_exposed"),
            },
        ),
        _readiness_item(
            check_id="safe_http_transport_errors",
            status="passed"
            if all(
                item.get("status") == "error" and item.get("raw_details_exposed") is False
                for item in http_transport_failure_smoke.values()
            )
            else "blocked",
            summary="HTTP 认证、服务端、连接和超时错误均脱敏",
            evidence={
                case: {
                    "error_type": item.get("error_type"),
                    "raw_details_exposed": item.get("raw_details_exposed"),
                }
                for case, item in http_transport_failure_smoke.items()
            },
        ),
    ]

    http_tools = [tool for tool in runtime_status.get("tools") or [] if tool.get("data_source") == "http"]
    http_integration_modes = {
        tool.get("integration_mode") for tool in http_tools if tool.get("integration_mode")
    }
    if len(http_tools) == 2 and http_integration_modes == {"fake_http"}:
        http_summary = "风控和毛利均通过进程内 fake HTTP transport 验证 HTTP client 链路"
    elif len(http_tools) == 2 and http_integration_modes == {"external_http"}:
        http_summary = "风控和毛利均已切到外部真实 HTTP 接口"
    elif len(http_tools) == 2:
        http_summary = "风控和毛利均已切到 HTTP 模式，但集成模式不一致"
    else:
        http_summary = "当前仍有工具处于 mock 模式；接真实系统前需配置 Base URL"
    items.append(
        _readiness_item(
            check_id="real_http_configured",
            status="passed" if len(http_tools) == 2 else "warning",
            summary=http_summary,
            evidence={
                "fake_http": http_integration_modes == {"fake_http"},
                "integration_modes": sorted(http_integration_modes),
                "tool_sources": [
                    {
                        "tool_name": tool.get("tool_name"),
                        "data_source": tool.get("data_source"),
                        "integration_mode": tool.get("integration_mode"),
                        "base_url_configured": tool.get("base_url_configured"),
                        "api_key_configured": tool.get("api_key_configured"),
                    }
                    for tool in runtime_status.get("tools") or []
                ]
            },
        )
    )
    items.append(
        _readiness_item(
            check_id="external_http_configured",
            status="passed"
            if len(http_tools) == 2 and http_integration_modes == {"external_http"}
            else "warning",
            summary="风控和毛利均已指向外部真实 HTTP 系统"
            if len(http_tools) == 2 and http_integration_modes == {"external_http"}
            else "上线前仍需用外部真实 HTTP 系统配置补跑严格门禁",
            evidence={
                "external_http_ready": len(http_tools) == 2
                and http_integration_modes == {"external_http"},
                "integration_modes": sorted(http_integration_modes),
                "tool_sources": [
                    {
                        "tool_name": tool.get("tool_name"),
                        "data_source": tool.get("data_source"),
                        "integration_mode": tool.get("integration_mode"),
                        "base_url_configured": tool.get("base_url_configured"),
                    }
                    for tool in runtime_status.get("tools") or []
                ],
            },
        )
    )
    items.append(
        _readiness_item(
            check_id="access_control_enabled",
            status="passed"
            if runtime_status.get("access_control", {}).get("enabled")
            else "warning",
            summary="访问控制已启用"
            if runtime_status.get("access_control", {}).get("enabled")
            else "接真实订单数据前建议启用访问控制 token",
            evidence={
                "enabled": runtime_status.get("access_control", {}).get("enabled"),
                "ready": runtime_status.get("access_control", {}).get("ready"),
                "missing_scopes": runtime_status.get("access_control", {}).get(
                    "missing_scopes"
                ),
            },
        )
    )
    items.append(
        _readiness_item(
            check_id="persistent_audit_enabled",
            status="passed" if audit_file else "warning",
            summary="本次 smoke 已验证 JSONL 文件审计"
            if audit_file
            else "本次 smoke 未传入 --audit-file；只验证内存审计",
            evidence={"audit_file_checked": bool(audit_file)},
        )
    )
    items.append(_sample_validation_readiness_item(sample_validations))

    blockers = [item for item in items if item["status"] == "blocked"]
    warnings = [item for item in items if item["status"] == "warning"]
    passed = [item for item in items if item["status"] == "passed"]
    overall_status = "blocked" if blockers else ("ready_with_warnings" if warnings else "ready")

    return {
        "overall_status": overall_status,
        "passed": [item["id"] for item in passed],
        "warnings": [item["id"] for item in warnings],
        "blockers": [item["id"] for item in blockers],
        "items": items,
    }


def _audit_traceability_readiness_item(
    *,
    query_smoke: Dict[str, Any],
    audit_events: list[Dict[str, Any]],
) -> Dict[str, Any]:
    """Check that the natural-language tool call has reconstructable safe audit evidence."""
    audit_id = (query_smoke.get("tool_call") or {}).get("audit_id")
    event = next((item for item in audit_events if item.get("audit_id") == audit_id), None)
    has_selection_reason = bool(event and event.get("selection_reason"))
    has_confidence = bool(event and isinstance(event.get("confidence"), (int, float)))
    status = "passed" if event and has_selection_reason and has_confidence else "blocked"
    return _readiness_item(
        check_id="audit_traceability",
        status=status,
        summary="自然语言工具调用审计包含安全选择依据、置信度和可关联 Audit ID"
        if status == "passed"
        else "自然语言工具调用审计缺少选择依据、置信度或可关联 Audit ID",
        evidence={
            "audit_id": audit_id if str(audit_id or "").startswith("bt-") else None,
            "event_found": bool(event),
            "has_selection_reason": has_selection_reason,
            "has_confidence": has_confidence,
        },
    )


def _sample_validation_readiness_item(sample_validations: Dict[str, Any]) -> Dict[str, Any]:
    if not sample_validations:
        return _readiness_item(
            check_id="captured_sample_validation",
            status="warning",
            summary="未提供真实系统响应样例；接入前建议用 --risk-response-file/--profit-response-file 校验",
            evidence={"validated_samples": []},
        )

    invalid_samples = {
        name: {
            "status": result.get("status"),
            "diagnostic_code": result.get("diagnostic_code"),
            "missing_fields": result.get("missing_fields", []),
            "invalid_fields": result.get("invalid_fields", []),
        }
        for name, result in sample_validations.items()
        if result.get("status") != "valid"
    }
    ignored_result_keys = {
        name: result.get("ignored_result_keys", [])
        for name, result in sample_validations.items()
        if result.get("status") == "valid" and result.get("ignored_result_keys")
    }
    return _readiness_item(
        check_id="captured_sample_validation",
        status="blocked" if invalid_samples else "passed",
        summary="真实系统响应样例未通过合同校验"
        if invalid_samples
        else "已提供的真实系统响应样例均通过合同校验",
        evidence={
            "validated_samples": sorted(sample_validations.keys()),
            "invalid_samples": invalid_samples,
            "ignored_result_keys": ignored_result_keys,
        },
    )


def _readiness_item(
    *,
    check_id: str,
    status: str,
    summary: str,
    evidence: Dict[str, Any],
) -> Dict[str, Any]:
    if status not in {"passed", "warning", "blocked"}:
        raise ValueError(f"Unsupported readiness status: {status}")
    return {
        "id": check_id,
        "status": status,
        "summary": summary,
        "evidence": evidence,
    }


def _runtime_status_summary(status: Dict[str, Any]) -> Dict[str, Any]:
    """Return the safe runtime status fields that matter for integration smoke."""
    business_tools = status.get("business_tools") or {}
    access_control = status.get("access_control") or {}
    llm_intent = status.get("llm_intent") or {}
    return {
        "status": status.get("status"),
        "business_tools": {
            "enabled": business_tools.get("enabled"),
            "timeout_seconds": business_tools.get("timeout_seconds"),
            "tool_count": business_tools.get("tool_count"),
        },
        "access_control": {
            "enabled": access_control.get("enabled"),
            "ready": access_control.get("ready"),
            "missing_scopes": access_control.get("missing_scopes") or [],
        },
        "llm_intent": {
            "enabled": llm_intent.get("enabled"),
            "min_confidence": llm_intent.get("min_confidence"),
            "model_configured": llm_intent.get("model_configured"),
        },
        "tools": [
            {
                "tool_name": tool.get("tool_name"),
                "scene_type": tool.get("scene_type"),
                "data_source": tool.get("data_source"),
                "integration_mode": tool.get("integration_mode"),
                "endpoint_template": tool.get("endpoint_template"),
                "base_url_configured": tool.get("base_url_configured"),
                "api_key_configured": tool.get("api_key_configured"),
                "contract_available": tool.get("contract_available"),
            }
            for tool in status.get("tools") or []
        ],
    }


def _validate_response_file(
    *,
    service: Any,
    tool_name: str,
    path: str,
) -> Dict[str, Any]:
    response_path = Path(path)
    if not response_path.is_file():
        raise AssertionError(f"Response sample file does not exist: {path}")

    try:
        payload = json.loads(response_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Response sample file is not valid JSON: {path}") from exc

    result = service.validate_response_contract(tool_name=tool_name, payload=payload)
    encoded_result = json.dumps(result, ensure_ascii=False)
    for value in _sample_scalar_values(payload):
        if value and value in encoded_result:
            raise AssertionError("Response sample validation leaked submitted payload values")

    return {
        "file": str(response_path),
        "tool": result.get("name"),
        "status": result.get("status"),
        "error_type": result.get("error_type"),
        "diagnostic_code": result.get("diagnostic_code"),
        "missing_fields": result.get("missing_fields", []),
        "invalid_fields": result.get("invalid_fields", []),
        "exposed_result_keys": result.get("exposed_result_keys", []),
        "ignored_result_keys": result.get("ignored_result_keys", []),
        "payload_values_exposed": False,
    }


def _sample_scalar_values(payload: Any) -> list[str]:
    if isinstance(payload, dict):
        values = []
        for value in payload.values():
            values.extend(_sample_scalar_values(value))
        return values
    if isinstance(payload, list):
        values = []
        for item in payload:
            values.extend(_sample_scalar_values(item))
        return values
    if isinstance(payload, (str, int, float, bool)) and payload is not None:
        return [str(payload)]
    return []


def _run_contract_failure_smoke(*, service: Any, order_id: str) -> Dict[str, Any]:
    """Validate safe diagnostics for a real-system response contract failure."""
    invalid_profit_payload = {
        "order_id": order_id,
        "gross_amount": 128.6,
        "platform_commission": 19.29,
        "driver_income": 92.35,
        "subsidy": 8.0,
        "coupon": 6.0,
    }
    result = service.validate_response_contract(
        tool_name=PROFIT_TOOL_NAME,
        payload=invalid_profit_payload,
    )
    if result.get("status") != "invalid":
        raise AssertionError("Invalid profit sample unexpectedly passed validation")
    if result.get("diagnostic_code") != "missing_required_fields":
        raise AssertionError(f"Unexpected diagnostic_code: {result.get('diagnostic_code')}")
    if result.get("missing_fields") != ["platform_net_profit"]:
        raise AssertionError(f"Unexpected missing_fields: {result.get('missing_fields')}")

    encoded = json.dumps(result, ensure_ascii=False)
    leaked_values = [
        str(value)
        for value in invalid_profit_payload.values()
        if value != order_id and not isinstance(value, str)
    ]
    if order_id in encoded or any(value in encoded for value in leaked_values):
        raise AssertionError("Contract failure diagnostic leaked submitted payload values")

    return {
        "tool": result.get("name"),
        "status": result.get("status"),
        "error_type": result.get("error_type"),
        "diagnostic_code": result.get("diagnostic_code"),
        "missing_fields": result.get("missing_fields"),
        "invalid_fields": result.get("invalid_fields"),
        "payload_values_exposed": False,
    }


def _run_runtime_failure_smoke(*, service: Any, query: str) -> Dict[str, Any]:
    """Validate safe degradation when a business system call fails at runtime."""
    original_tool = service._tools[PROFIT_TOOL_NAME]

    def raise_runtime_error(_order_id: str) -> Dict[str, Any]:
        raise RuntimeError(RUNTIME_FAILURE_MESSAGE)

    service._tools[PROFIT_TOOL_NAME] = original_tool.__class__(
        name=original_tool.name,
        label=original_tool.label,
        scene_type=original_tool.scene_type,
        description=original_tool.description,
        executor=raise_runtime_error,
    )
    try:
        tool_calls = service.maybe_execute(query=query, scene_type="profit")
    finally:
        service._tools[PROFIT_TOOL_NAME] = original_tool

    if len(tool_calls) != 1:
        raise AssertionError(f"Expected one degraded profit tool call, got {len(tool_calls)}")
    call = tool_calls[0]
    if call.get("status") != "error":
        raise AssertionError(f"Runtime failure smoke did not degrade: {call.get('status')}")
    if call.get("error_type") != "RuntimeError":
        raise AssertionError(f"Unexpected runtime error_type: {call.get('error_type')}")
    if call.get("result") != {}:
        raise AssertionError("Runtime failure smoke exposed a result payload")
    expected_summary = "订单毛利链路调用失败，请稍后重试或联系系统管理员。"
    if call.get("summary") != expected_summary:
        raise AssertionError(f"Unexpected degraded summary: {call.get('summary')}")

    tool_context = service.format_tool_context(tool_calls)
    encoded_call = json.dumps(call, ensure_ascii=False)
    if RUNTIME_FAILURE_MESSAGE in encoded_call or RUNTIME_FAILURE_MESSAGE in tool_context:
        raise AssertionError("Runtime failure exposed raw exception details")
    if "错误类型: RuntimeError" not in tool_context:
        raise AssertionError("Runtime failure context missing safe error type")

    audit_event = _find_audit_event_by_id(
        events=service.list_audit_events(limit=10),
        audit_id=call.get("audit_id"),
    )
    encoded_event = json.dumps(audit_event, ensure_ascii=False)
    if audit_event.get("status") != "error":
        raise AssertionError("Runtime failure audit event missing error status")
    if audit_event.get("error_type") != "RuntimeError":
        raise AssertionError("Runtime failure audit event missing error_type")
    if RUNTIME_FAILURE_MESSAGE in encoded_event:
        raise AssertionError("Runtime failure audit event leaked raw exception details")

    return {
        "tool": call.get("name"),
        "status": call.get("status"),
        "error_type": call.get("error_type"),
        "audit_id": call.get("audit_id"),
        "has_empty_result": call.get("result") == {},
        "summary_is_safe": RUNTIME_FAILURE_MESSAGE not in str(call.get("summary")),
        "tool_context_checks": {
            "has_error_type": "错误类型: RuntimeError" in tool_context,
            "raw_error_exposed": False,
        },
        "audit_checks": {
            "status": audit_event.get("status"),
            "error_type": audit_event.get("error_type"),
            "raw_error_exposed": False,
        },
    }


def _run_unsafe_order_id_smoke(*, service: Any) -> Dict[str, Any]:
    """Validate that unsafe order identifiers do not render paths or execute tools."""
    unsafe_order_id = "../admin?token=secret"
    try:
        service.probe(tool_name=PROFIT_TOOL_NAME, order_id=unsafe_order_id)
    except ValueError as exc:
        probe_error = str(exc)
    else:
        raise AssertionError("Unsafe order id probe unexpectedly succeeded")

    if probe_error != "order_id contains unsupported characters":
        raise AssertionError(f"Unexpected unsafe order id error: {probe_error}")
    if "secret" in probe_error or "../admin" in probe_error:
        raise AssertionError("Unsafe order id error leaked submitted value")

    original_llm_enabled = settings.enable_business_tool_llm_intent
    original_min_confidence = settings.business_tool_llm_intent_min_confidence
    original_llm_client = service.llm_client

    class FakeChatCompletions:
        def create(self, **_kwargs: Any) -> Any:
            return type(
                "FakeResponse",
                (),
                {
                    "choices": [
                        type(
                            "Choice",
                            (),
                            {
                                "message": type(
                                    "Message",
                                    (),
                                    {
                                        "content": json.dumps(
                                            {
                                                "tool_name": PROFIT_TOOL_NAME,
                                                "order_id": unsafe_order_id,
                                                "confidence": 0.91,
                                                "reason": "model supplied unsafe id",
                                                "missing_fields": [],
                                            }
                                        )
                                    },
                                )()
                            },
                        )()
                    ]
                },
            )()

    try:
        settings.enable_business_tool_llm_intent = True
        settings.business_tool_llm_intent_min_confidence = 0.75
        service.llm_client = type(
            "FakeLlmClient",
            (),
            {"chat": type("Chat", (), {"completions": FakeChatCompletions()})()},
        )()
        intent = service.inspect_intent(query="查一下这个单的钱流", scene_type="profit")
        calls = service.maybe_execute(query="查一下这个单的钱流", scene_type="profit")
    finally:
        settings.enable_business_tool_llm_intent = original_llm_enabled
        settings.business_tool_llm_intent_min_confidence = original_min_confidence
        service.llm_client = original_llm_client

    encoded_intent = json.dumps(intent, ensure_ascii=False)
    if unsafe_order_id in encoded_intent:
        raise AssertionError("Unsafe LLM order id leaked through intent")
    if intent.get("order_id") is not None:
        raise AssertionError("Unsafe LLM order id was accepted")
    if intent.get("missing_fields") != ["order_id"]:
        raise AssertionError(f"Unsafe LLM order id did not request order id: {intent}")
    if calls:
        raise AssertionError("Unsafe LLM order id unexpectedly executed a tool")

    return {
        "probe_status": "rejected",
        "probe_error": probe_error,
        "llm_intent": {
            "tool_name": intent.get("tool_name"),
            "order_id": intent.get("order_id"),
            "missing_fields": intent.get("missing_fields"),
            "needs_clarification": intent.get("needs_clarification"),
        },
        "tool_call_count": len(calls),
        "unsafe_value_exposed": False,
    }


def _run_http_transport_failure_smoke(*, order_id: str) -> Dict[str, Any]:
    """Validate safe HTTP transport failure classification without network I/O."""
    cases = [
        ("http_401", _raise_http_error(401, order_id), "ConnectionError"),
        ("http_500", _raise_http_error(500, order_id), "ConnectionError"),
        ("url_error", _raise_url_error, "ConnectionError"),
        ("timeout", _raise_timeout_error(order_id), "TimeoutError"),
    ]
    results = {}
    original_urlopen = business_clients.request.urlopen
    try:
        for name, fake_urlopen, expected_error_type in cases:
            business_clients.request.urlopen = fake_urlopen
            result = _run_one_transport_failure_case(
                order_id=order_id,
                expected_error_type=expected_error_type,
            )
            results[name] = result
    finally:
        business_clients.request.urlopen = original_urlopen

    return results


def _raise_http_error(status_code: int, order_id: str):
    def fake_urlopen(_req: Any, timeout: int) -> Any:
        raise HTTPError(
            url=(
                f"https://{HTTP_TRANSPORT_HOST}/profit/orders/"
                f"{order_id}/chain?token={HTTP_TRANSPORT_SECRET}"
            ),
            code=status_code,
            msg=f"Unauthorized token={HTTP_TRANSPORT_SECRET}",
            hdrs=None,
            fp=None,
        )

    return fake_urlopen


def _fake_http_urlopen_from_local_routes(req: Any, timeout: int) -> Any:
    path = req.full_url.replace(LOCAL_FAKE_HTTP_BASE_URL, "")
    if path == endpoint_path(RISK_TOOL_NAME, order_id="ORD88888"):
        payload = fake_risk_payload("ORD88888")
    elif path == endpoint_path(PROFIT_TOOL_NAME, order_id="ORD88888"):
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


def _raise_url_error(_req: Any, timeout: int) -> Any:
    raise URLError(f"dns failed for {HTTP_TRANSPORT_HOST} token={HTTP_TRANSPORT_SECRET}")


def _raise_timeout_error(order_id: str):
    def fake_urlopen(_req: Any, timeout: int) -> Any:
        raise TimeoutError(f"timeout for {order_id} token={HTTP_TRANSPORT_SECRET}")

    return fake_urlopen


def _run_one_transport_failure_case(
    *,
    order_id: str,
    expected_error_type: str,
) -> Dict[str, Any]:
    client = ProfitSystemClient(
        base_url=f"https://{HTTP_TRANSPORT_HOST}",
        api_key=HTTP_TRANSPORT_SECRET,
        timeout=1,
    )
    try:
        client.get_chain_detail(order_id)
    except Exception as exc:
        error_type = type(exc).__name__
        message = str(exc)
    else:
        raise AssertionError("HTTP transport failure case unexpectedly succeeded")

    if error_type != expected_error_type:
        raise AssertionError(f"Unexpected HTTP transport error type: {error_type}")
    forbidden_texts = [
        HTTP_TRANSPORT_SECRET,
        HTTP_TRANSPORT_HOST,
        order_id,
        "Unauthorized",
        "dns failed",
    ]
    if any(text and text in message for text in forbidden_texts):
        raise AssertionError("HTTP transport failure exposed sensitive details")

    return {
        "status": "error",
        "error_type": error_type,
        "safe_message": message,
        "raw_details_exposed": False,
    }


def _run_profit_query_smoke(
    *,
    service: Any,
    query: str,
    order_id: str,
) -> Dict[str, Any]:
    """Validate that a natural-language profit query triggers the business tool."""
    intent = service.inspect_intent(query=query, scene_type="profit")
    if intent.get("tool_name") != PROFIT_TOOL_NAME:
        raise AssertionError(f"Profit query selected wrong tool: {intent.get('tool_name')}")
    if intent.get("needs_clarification"):
        raise AssertionError(f"Profit query unexpectedly needs clarification: {intent}")
    if intent.get("order_id") != order_id:
        raise AssertionError(f"Profit query extracted wrong order_id: {intent.get('order_id')}")

    tool_calls = service.execute_intent(intent)
    if len(tool_calls) != 1:
        raise AssertionError(f"Expected one profit tool call, got {len(tool_calls)}")
    call = tool_calls[0]
    _assert_profit_tool_call_success(call=call, order_id=order_id)

    tool_context = service.format_tool_context(tool_calls)
    for expected_text in (
        "【工具 1】订单毛利链路",
        f"接口路径: /profit/orders/{order_id}/chain",
        "- platform_commission:",
        "- driver_income:",
        "- platform_net_profit:",
        "- chain:",
    ):
        if expected_text not in tool_context:
            raise AssertionError(f"Tool context missing expected text: {expected_text}")

    return {
        "query": query,
        "intent": {
            "tool_name": intent.get("tool_name"),
            "order_id": intent.get("order_id"),
            "confidence": intent.get("confidence"),
            "needs_clarification": intent.get("needs_clarification"),
        },
        "execution_path": "inspected_intent",
        "tool_call": _probe_summary(call),
        "tool_context_checks": {
            "has_endpoint_path": f"/profit/orders/{order_id}/chain" in tool_context,
            "has_profit_fields": all(
                field in tool_context
                for field in (
                    "platform_commission",
                    "driver_income",
                    "platform_net_profit",
                    "chain",
                )
            ),
        },
    }


def _assert_profit_tool_call_success(*, call: Dict[str, Any], order_id: str) -> None:
    if call.get("name") != PROFIT_TOOL_NAME:
        raise AssertionError(f"Unexpected profit tool call: {call.get('name')}")
    if call.get("status") != "success":
        raise AssertionError(f"Profit query tool call failed: {call.get('error_type')}")
    if call.get("endpoint_path") != f"/profit/orders/{order_id}/chain":
        raise AssertionError(f"Unexpected endpoint_path: {call.get('endpoint_path')}")
    if call.get("arguments") != {"order_id": order_id}:
        raise AssertionError(f"Unexpected arguments: {call.get('arguments')}")

    result = call.get("result") or {}
    missing_fields = [field for field in PROFIT_REQUIRED_FIELDS if field not in result]
    if missing_fields:
        raise AssertionError(f"Profit query result missing fields: {missing_fields}")
    if not result.get("chain"):
        raise AssertionError("Profit query result missing display chain")


def _assert_probe_success(
    label: str,
    probe: Dict[str, Any],
    required_fields: Dict[str, Any],
) -> None:
    if probe.get("status") != "success":
        raise AssertionError(f"{label} probe failed: {probe.get('error_type')}")
    if not str(probe.get("audit_id", "")).startswith("bt-"):
        raise AssertionError(f"{label} probe missing audit_id")

    result = probe.get("result") or {}
    missing_fields = [field for field in required_fields if field not in result]
    if missing_fields:
        raise AssertionError(f"{label} probe missing result fields: {missing_fields}")


def _assert_safe_audit_events(
    *,
    events: list[Dict[str, Any]],
    order_id: str,
    expected_count: int,
) -> None:
    if len(events) < expected_count:
        raise AssertionError(f"Expected at least {expected_count} audit events, got {len(events)}")
    encoded = json.dumps(events, ensure_ascii=False)
    if order_id in encoded:
        raise AssertionError("Audit events leaked raw order_id")
    for event in events[:expected_count]:
        if not str(event.get("audit_id", "")).startswith("bt-"):
            raise AssertionError("Audit event missing audit_id")
        if event.get("arguments", {}).get("order_id") == order_id:
            raise AssertionError("Audit event contains raw order_id argument")


def _assert_audit_file_safe(
    *,
    audit_file: str,
    order_id: str,
    forbidden_texts: Optional[list[str]] = None,
) -> None:
    path = Path(audit_file)
    if not path.exists():
        raise AssertionError(f"Audit file was not written: {audit_file}")
    content = path.read_text(encoding="utf-8")
    if order_id in content:
        raise AssertionError("Audit file leaked raw order_id")
    for text in forbidden_texts or []:
        if text and text in content:
            raise AssertionError("Audit file leaked forbidden runtime failure detail")
    lines = [line for line in content.splitlines() if line.strip()]
    if not lines:
        raise AssertionError("Audit file is empty")
    for line in lines:
        event = json.loads(line)
        if not str(event.get("audit_id", "")).startswith("bt-"):
            raise AssertionError("Audit file event missing audit_id")


def _find_audit_event_by_id(
    *,
    events: list[Dict[str, Any]],
    audit_id: Any,
) -> Dict[str, Any]:
    for event in events:
        if event.get("audit_id") == audit_id:
            return event
    raise AssertionError(f"Audit event not found: {audit_id}")


def _probe_summary(probe: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tool": probe.get("name"),
        "status": probe.get("status"),
        "audit_id": probe.get("audit_id"),
        "data_source": probe.get("data_source"),
        "endpoint_path": probe.get("endpoint_path"),
        "duration_ms": probe.get("duration_ms"),
        "result_keys": sorted((probe.get("result") or {}).keys()),
    }


def _report_summary(report: Dict[str, Any]) -> Dict[str, Any]:
    """Return a compact, CI-friendly summary without raw order payload details."""
    readiness = report.get("readiness_check") or {}
    audit = report.get("audit") or {}
    return {
        "status": report.get("status"),
        "readiness": {
            "overall_status": readiness.get("overall_status"),
            "passed_count": len(readiness.get("passed") or []),
            "warning_count": len(readiness.get("warnings") or []),
            "blocker_count": len(readiness.get("blockers") or []),
            "warnings": readiness.get("warnings") or [],
            "blockers": readiness.get("blockers") or [],
        },
        "audit": {
            "event_count": audit.get("event_count"),
            "file_configured": bool(audit.get("file")),
        },
    }


def _write_json_report(*, path: str, report: Dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run business tool smoke checks")
    parser.add_argument("--order-id", default="ORD88888", help="Order id to probe")
    parser.add_argument(
        "--audit-file",
        default="",
        help="Optional JSONL audit file path to validate",
    )
    parser.add_argument(
        "--risk-response-file",
        default="",
        help="Optional captured risk response JSON file to validate",
    )
    parser.add_argument(
        "--profit-response-file",
        default="",
        help="Optional captured profit response JSON file to validate",
    )
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="Return exit code 2 when readiness_check.overall_status is blocked.",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help=(
            "Return non-zero unless readiness_check.overall_status is ready "
            "(2 for blocked, 3 for ready_with_warnings)."
        ),
    )
    parser.add_argument(
        "--output-file",
        default="",
        help="Optional JSON file path for the full smoke report.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only a compact readiness summary to stdout.",
    )
    parser.add_argument(
        "--fake-http",
        action="store_true",
        help="Run smoke through an in-process fake HTTP transport for risk/profit clients.",
    )
    args = parser.parse_args()

    report = run_smoke(
        order_id=args.order_id,
        audit_file=args.audit_file or None,
        risk_response_file=args.risk_response_file or None,
        profit_response_file=args.profit_response_file or None,
        use_fake_http=args.fake_http,
    )
    if args.output_file:
        _write_json_report(path=args.output_file, report=report)

    stdout_report = _report_summary(report) if args.summary_only else report
    print(json.dumps(stdout_report, ensure_ascii=False, indent=2, sort_keys=True))
    overall_status = report.get("readiness_check", {}).get("overall_status")
    if overall_status == "blocked" and (args.fail_on_blocked or args.require_ready):
        return 2
    if overall_status == "ready_with_warnings" and args.require_ready:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
