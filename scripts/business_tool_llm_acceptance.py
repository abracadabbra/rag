"""
Live acceptance check for business-tool LLM intent fallback.

This script intentionally performs real LLM calls. It is not part of the
default smoke suite because it depends on a configured provider credential.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.config import settings
from api.services.business_contracts import PROFIT_TOOL_NAME
from api.services.tool_service import reset_tool_service, get_tool_service


def run_acceptance(*, order_id: str, low_confidence: float) -> Dict[str, Any]:
    """Run real LLM fallback acceptance without executing business APIs."""
    order_id = (order_id or "").strip()
    if not order_id:
        raise ValueError("order_id is required")
    if not 0 <= low_confidence <= 1:
        raise ValueError("low_confidence must be between 0 and 1")

    previous_llm_enabled = settings.enable_business_tool_llm_intent
    previous_min_confidence = settings.business_tool_llm_intent_min_confidence

    try:
        settings.enable_business_tool_llm_intent = True
        reset_tool_service()
        service = get_tool_service()
        initial_status = service.runtime_status().get("llm_intent") or {}

        high_confidence_query = f"看看订单 {order_id} 的费用是怎么分的"
        high_confidence_intent = service.inspect_intent(
            query=high_confidence_query,
            scene_type="profit",
        )

        settings.business_tool_llm_intent_min_confidence = low_confidence
        low_confidence_query = f"看看订单 {order_id} 的钱是怎么分的"
        low_confidence_intent = service.inspect_intent(
            query=low_confidence_query,
            scene_type="profit",
        )
        low_confidence_calls = service.execute_intent(low_confidence_intent)

        invalid_order_query = "看看订单 ../admin?token=secret 的费用是怎么分的"
        invalid_order_intent = service.inspect_intent(
            query=invalid_order_query,
            scene_type="profit",
        )
        invalid_order_calls = service.execute_intent(invalid_order_intent)
        final_status = service.runtime_status().get("llm_intent") or {}

        high_confidence_passed = _is_profit_llm_intent(
            high_confidence_intent,
            order_id=order_id,
        ) and not high_confidence_intent.get("needs_clarification")
        low_confidence_passed = (
            _is_profit_llm_intent(low_confidence_intent, order_id=order_id)
            and low_confidence_intent.get("needs_clarification") is True
            and "tool_intent_confirmation"
            in (low_confidence_intent.get("missing_fields") or [])
            and low_confidence_calls == []
        )
        invalid_order_passed = (
            invalid_order_intent.get("needs_clarification") is True
            and "order_id" in (invalid_order_intent.get("missing_fields") or [])
            and invalid_order_intent.get("order_id") is None
            and invalid_order_calls == []
        )
        telemetry_passed = (
            final_status.get("enabled") is True
            and final_status.get("model_configured") is True
            and final_status.get("last_status") == "success"
            and int(final_status.get("success_count") or 0) >= 1
        )

        checks = {
            "high_confidence_tool_intent": high_confidence_passed,
            "low_confidence_clarification": low_confidence_passed,
            "invalid_order_id_not_executed": invalid_order_passed,
            "runtime_telemetry_recorded": telemetry_passed,
        }
        return {
            "status": "ok" if all(checks.values()) else "failed",
            "checks": checks,
            "config": {
                "provider": settings.llm_provider,
                "model_configured": bool(initial_status.get("model_configured")),
                "low_confidence_threshold": low_confidence,
            },
            "intents": {
                "high_confidence": _intent_summary(high_confidence_intent),
                "low_confidence": _intent_summary(low_confidence_intent),
                "invalid_order": _intent_summary(invalid_order_intent),
            },
            "executed_call_counts": {
                "low_confidence": len(low_confidence_calls),
                "invalid_order": len(invalid_order_calls),
            },
            "llm_intent_runtime": _llm_runtime_summary(final_status),
        }
    finally:
        settings.enable_business_tool_llm_intent = previous_llm_enabled
        settings.business_tool_llm_intent_min_confidence = previous_min_confidence
        reset_tool_service()


def _is_profit_llm_intent(intent: Dict[str, Any], *, order_id: str) -> bool:
    return (
        intent.get("tool_name") == PROFIT_TOOL_NAME
        and intent.get("selection_source") == "llm"
        and intent.get("order_id") == order_id
        and isinstance(intent.get("confidence"), (int, float))
    )


def _intent_summary(intent: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tool_name": intent.get("tool_name"),
        "selection_source": intent.get("selection_source"),
        "order_id_present": bool(intent.get("order_id")),
        "confidence": intent.get("confidence"),
        "missing_fields": intent.get("missing_fields") or [],
        "needs_clarification": intent.get("needs_clarification"),
    }


def _llm_runtime_summary(status: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "enabled": bool(status.get("enabled")),
        "model_configured": bool(status.get("model_configured")),
        "attempt_count": int(status.get("attempt_count") or 0),
        "success_count": int(status.get("success_count") or 0),
        "error_count": int(status.get("error_count") or 0),
        "last_status": status.get("last_status"),
        "last_resolution": status.get("last_resolution"),
        "last_error_type": status.get("last_error_type"),
    }


def _write_json_report(*, path: str, report: Dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run live business-tool LLM intent fallback acceptance"
    )
    parser.add_argument("--order-id", default="ORD88888", help="Safe order id for LLM intent checks")
    parser.add_argument(
        "--low-confidence-threshold",
        type=float,
        default=0.99,
        help="Temporary threshold used to force the low-confidence clarification case.",
    )
    parser.add_argument("--output-file", default="", help="Optional JSON report path")
    args = parser.parse_args()

    report = run_acceptance(
        order_id=args.order_id,
        low_confidence=args.low_confidence_threshold,
    )
    if args.output_file:
        _write_json_report(path=args.output_file, report=report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.get("status") == "ok" else 4


if __name__ == "__main__":
    raise SystemExit(main())
