"""
Build a machine-readable business-tool integration acceptance pack.

The pack is meant for real risk/profit system handoff. It combines the current
contract snapshot with the safe smoke/readiness report and concrete next steps,
without echoing raw business response payloads.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.services.business_contracts import contract_snapshot
from api.services.prompt_templates import business_prompt_contract_snapshot
from scripts.business_tool_smoke import run_smoke


def build_acceptance_pack(
    *,
    order_id: str,
    audit_file: Optional[str] = None,
    risk_response_file: Optional[str] = None,
    profit_response_file: Optional[str] = None,
    use_fake_http: bool = False,
) -> Dict[str, Any]:
    """Return a safe handoff pack for business-tool integration acceptance."""
    contracts = contract_snapshot()
    try:
        smoke_report = run_smoke(
            order_id=order_id,
            audit_file=audit_file,
            risk_response_file=risk_response_file,
            profit_response_file=profit_response_file,
            use_fake_http=use_fake_http,
        )
    except Exception as exc:  # pragma: no cover - exercised through tests.
        return _blocked_pack_from_smoke_error(contracts=contracts, error=exc)

    readiness = smoke_report.get("readiness_check") or {}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": _pack_status(readiness),
        "acceptance_scope": [
            "contract_snapshot",
            "intent_precheck",
            "business_tool_probe",
            "readiness_gates",
            "safe_audit_traceability",
            "captured_response_sample_validation",
            "prompt_contract",
        ],
        "contracts": contracts,
        "prompt_contract": business_prompt_contract_snapshot(),
        "readiness_summary": {
            "overall_status": readiness.get("overall_status"),
            "passed": readiness.get("passed") or [],
            "warnings": readiness.get("warnings") or [],
            "blockers": readiness.get("blockers") or [],
        },
        "readiness_items": readiness.get("items") or [],
        "safe_smoke_evidence": _safe_smoke_evidence(smoke_report),
        "integration_handoff": _integration_handoff(readiness),
        "sample_handoff": _sample_handoff(),
        "source_commands": _source_commands(),
    }


def _blocked_pack_from_smoke_error(
    *,
    contracts: Dict[str, Any],
    error: Exception,
) -> Dict[str, Any]:
    error_evidence = _safe_smoke_error_evidence(error)
    readiness_item = {
        "id": "smoke_execution",
        "status": "blocked",
        "summary": "smoke/readiness 执行失败；需先修复当前业务工具运行态",
        "evidence": error_evidence,
    }
    readiness = {
        "overall_status": "blocked",
        "passed": [],
        "warnings": [],
        "blockers": ["smoke_execution"],
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "blocked",
        "acceptance_scope": [
            "contract_snapshot",
            "intent_precheck",
            "business_tool_probe",
            "readiness_gates",
            "safe_audit_traceability",
            "captured_response_sample_validation",
            "prompt_contract",
        ],
        "contracts": contracts,
        "prompt_contract": business_prompt_contract_snapshot(),
        "readiness_summary": readiness,
        "readiness_items": [readiness_item],
        "safe_smoke_evidence": {"smoke_execution": error_evidence},
        "integration_handoff": _integration_handoff(readiness),
        "sample_handoff": _sample_handoff(),
        "source_commands": _source_commands(),
    }


def _pack_status(readiness: Dict[str, Any]) -> str:
    overall_status = readiness.get("overall_status")
    if overall_status == "ready":
        return "accepted"
    if overall_status == "blocked":
        return "blocked"
    return "needs_attention"


def _safe_smoke_error_evidence(error: Exception) -> Dict[str, Any]:
    """Return actionable smoke failure evidence without raw runtime details."""
    error_type = error.__class__.__name__
    message = str(error)
    evidence: Dict[str, Any] = {
        "error_type": error_type,
        "diagnostic_code": "smoke_execution_failed",
    }

    if "Profit query tool call failed" in message:
        evidence.update(
            {
                "diagnostic_code": "profit_query_tool_call_failed",
                "tool": "get_profit_chain_detail",
                "safe_failure_type": _last_token(message),
                "suggested_action": (
                    "检查 PROFIT_API_BASE_URL / PROFIT_API_KEY，或使用 "
                    "BUSINESS_SMOKE_FAKE_HTTP=1 验证本地 HTTP 合同链路。"
                ),
            }
        )
    elif "risk probe failed" in message or "profit probe failed" in message:
        evidence.update(
            {
                "diagnostic_code": "probe_failed",
                "safe_failure_type": _last_token(message),
                "suggested_action": "使用 /api/v1/business-tools/probe 定点排查接口响应、鉴权和字段合同。",
            }
        )
    return evidence


def _last_token(text: str) -> str:
    token = (text.rsplit(":", 1)[-1] if ":" in text else text).strip()
    return token if token and len(token) <= 80 and token.replace("_", "").isalnum() else "unknown"


def _safe_smoke_evidence(report: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "runtime_status": report.get("runtime_status"),
        "probes": report.get("probes"),
        "intent_precheck_smoke": report.get("intent_precheck_smoke"),
        "query_smoke": {
            "execution_path": (report.get("query_smoke") or {}).get("execution_path"),
            "intent": (report.get("query_smoke") or {}).get("intent"),
            "tool_call": (report.get("query_smoke") or {}).get("tool_call"),
            "tool_context_checks": (report.get("query_smoke") or {}).get(
                "tool_context_checks"
            ),
        },
        "sample_validations": report.get("sample_validations") or {},
        "audit": {
            "event_count": (report.get("audit") or {}).get("event_count"),
            "audit_ids": (report.get("audit") or {}).get("audit_ids") or [],
            "file_configured": bool((report.get("audit") or {}).get("file")),
        },
        "fake_http": bool(report.get("fake_http")),
    }


def _integration_handoff(readiness: Dict[str, Any]) -> Dict[str, Any]:
    warnings = readiness.get("warnings") or []
    blockers = readiness.get("blockers") or []
    return {
        "go_live_allowed": readiness.get("overall_status") == "ready",
        "must_fix_before_real_order_traffic": blockers,
        "should_fix_before_production": warnings,
        "recommended_next_actions": _recommended_next_actions(
            warnings=warnings,
            blockers=blockers,
        ),
    }


def _sample_handoff() -> Dict[str, Any]:
    return {
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


def _source_commands() -> Dict[str, str]:
    return {
        "contract_export": "make business-contracts",
        "acceptance_pack": "make business-acceptance-pack",
        "fake_http_acceptance_pack": "make business-acceptance-pack BUSINESS_SMOKE_FAKE_HTTP=1",
        "sample_validation": "make business-validate-samples",
        "local_smoke": "make business-smoke",
        "strict_gate": "make business-smoke-strict",
        "llm_fallback_acceptance": "make business-llm-acceptance",
    }


def _recommended_next_actions(*, warnings: list[str], blockers: list[str]) -> list[str]:
    actions: list[str] = []
    active = set(warnings) | set(blockers)
    action_by_gate = {
        "real_http_configured": "配置 RISK_API_BASE_URL / PROFIT_API_BASE_URL，并用非生产订单号重新跑验收包。",
        "external_http_configured": "使用外部真实风控/毛利 Base URL 和非生产订单号补跑 make business-smoke-strict。",
        "access_control_enabled": "启用 ENABLE_BUSINESS_TOOL_ACCESS_CONTROL，并配置 read/execute token。",
        "persistent_audit_enabled": "启用 JSONL 或等价持久审计，并确认 audit_id 可回查。",
        "captured_sample_validation": "提供真实风控/毛利响应样例，用 RISK_RESPONSE_FILE / PROFIT_RESPONSE_FILE 离线校验。",
        "audit_traceability": "完成一次自然语言订单查询，确认 tool_calls.audit_id 能在脱敏审计中关联。",
        "llm_intent_fallback": "如果生产依赖模糊问题识别，配置有效 LLM 凭证并运行 make business-llm-acceptance。",
        "probe_endpoints": "先用 /business-tools/probe 定点排查真实接口响应、鉴权、超时或合同字段问题。",
        "smoke_execution": "先运行 make business-smoke 或 /business-tools/probe 定位当前运行态失败，再重新生成验收包。",
        "intent_precheck": "检查标准风控/毛利提示是否能在不执行接口的情况下选中目标工具。",
    }
    for gate in sorted(active):
        if gate in action_by_gate:
            actions.append(action_by_gate[gate])
    if not actions:
        actions.append("当前验收包已满足 go-live gate；进入小流量真实订单验证。")
    return actions


def write_json_report(*, path: str, report: Dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a business-tool integration acceptance pack."
    )
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
        "--fake-http",
        action="store_true",
        help="Run the pack through an in-process fake HTTP transport for risk/profit clients.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional JSON output path. Prints to stdout when omitted.",
    )
    args = parser.parse_args()

    pack = build_acceptance_pack(
        order_id=args.order_id,
        audit_file=args.audit_file or None,
        risk_response_file=args.risk_response_file or None,
        profit_response_file=args.profit_response_file or None,
        use_fake_http=args.fake_http,
    )
    if args.output:
        write_json_report(path=args.output, report=pack)
        print(f"Wrote business tool acceptance pack to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(pack, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
