"""
Validate captured business-system response JSON files against local contracts.

This is intentionally offline: it does not call risk/profit systems and does not
depend on the current runtime API base URLs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.services.business_clients import validate_business_response
from api.services.business_contracts import (
    BUSINESS_TOOL_RESULT_ALLOWLIST,
    BusinessContractError,
    PROFIT_TOOL_NAME,
    RISK_TOOL_NAME,
    derive_profit_chain,
)


def validate_response_samples(
    *,
    risk_response_file: Optional[str] = None,
    profit_response_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Return safe validation results for provided response sample files."""
    results: Dict[str, Any] = {}
    if risk_response_file:
        results["risk"] = _validate_response_file(
            tool_name=RISK_TOOL_NAME,
            path=risk_response_file,
        )
    if profit_response_file:
        results["profit"] = _validate_response_file(
            tool_name=PROFIT_TOOL_NAME,
            path=profit_response_file,
        )
    if not results:
        raise ValueError("At least one response sample file is required")

    invalid = [name for name, result in results.items() if result["status"] != "valid"]
    return {
        "status": "invalid" if invalid else "valid",
        "validated_samples": sorted(results.keys()),
        "invalid_samples": invalid,
        "results": results,
    }


def _validate_response_file(*, tool_name: str, path: str) -> Dict[str, Any]:
    response_path = Path(path)
    if not response_path.is_file():
        return {
            "file": str(response_path),
            "tool": tool_name,
            "status": "invalid",
            "error_type": "FileNotFoundError",
            "diagnostic_code": "missing_sample_file",
            "missing_fields": [],
            "invalid_fields": [],
            "exposed_result_keys": [],
            "ignored_result_keys": [],
        }

    try:
        payload = json.loads(response_path.read_text(encoding="utf-8"))
        validated = validate_business_response(tool_name, payload)
    except json.JSONDecodeError:
        return _invalid_result(
            path=response_path,
            tool_name=tool_name,
            error_type="JSONDecodeError",
            diagnostic_code="invalid_json",
        )
    except BusinessContractError as exc:
        return _invalid_result(
            path=response_path,
            tool_name=tool_name,
            error_type=exc.__class__.__name__,
            diagnostic_code=exc.diagnostic_code,
            missing_fields=exc.missing_fields,
            invalid_fields=exc.invalid_fields,
        )

    return {
        "file": str(response_path),
        "tool": tool_name,
        "status": "valid",
        "error_type": None,
        "diagnostic_code": None,
        "missing_fields": [],
        "invalid_fields": [],
        "exposed_result_keys": _exposed_result_keys(tool_name=tool_name, payload=validated),
        "ignored_result_keys": _ignored_result_keys(tool_name=tool_name, payload=validated),
    }


def _invalid_result(
    *,
    path: Path,
    tool_name: str,
    error_type: str,
    diagnostic_code: str,
    missing_fields: Optional[list[str]] = None,
    invalid_fields: Optional[list[str]] = None,
) -> Dict[str, Any]:
    return {
        "file": str(path),
        "tool": tool_name,
        "status": "invalid",
        "error_type": error_type,
        "diagnostic_code": diagnostic_code,
        "missing_fields": missing_fields or [],
        "invalid_fields": invalid_fields or [],
        "exposed_result_keys": [],
        "ignored_result_keys": [],
    }


def _exposed_result_keys(*, tool_name: str, payload: Dict[str, Any]) -> list[str]:
    allowlist = BUSINESS_TOOL_RESULT_ALLOWLIST.get(tool_name) or {}
    keys = {key for key in allowlist if key in payload}
    if tool_name == PROFIT_TOOL_NAME and ("chain" in payload or derive_profit_chain(payload)):
        keys.add("chain")
        keys.add("chain_source")
    return sorted(keys)


def _ignored_result_keys(*, tool_name: str, payload: Dict[str, Any]) -> list[str]:
    allowlist = BUSINESS_TOOL_RESULT_ALLOWLIST.get(tool_name) or {}
    exposed = set(_exposed_result_keys(tool_name=tool_name, payload=payload))
    return sorted(
        key
        for key in payload
        if key not in allowlist and key not in exposed
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate captured business response samples offline."
    )
    parser.add_argument(
        "--risk-response-file",
        default="",
        help="Captured risk response JSON file to validate.",
    )
    parser.add_argument(
        "--profit-response-file",
        default="",
        help="Captured profit response JSON file to validate.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional JSON output path. Prints to stdout when omitted.",
    )
    args = parser.parse_args()

    report = validate_response_samples(
        risk_response_file=args.risk_response_file or None,
        profit_response_file=args.profit_response_file or None,
    )
    content = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"{content}\n", encoding="utf-8")
        print(f"Wrote business response sample validation to {output_path}", file=sys.stderr)
    else:
        print(content)
    return 1 if report["status"] == "invalid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
