"""
Export the current business-tool contract snapshot as JSON.

This gives integrators and CI a machine-readable artifact without duplicating
the contract source of truth from api.services.business_contracts.
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

from api.services.business_contracts import contract_snapshot


def export_contracts(*, compact: bool = False) -> str:
    """Return the business-tool contract snapshot as stable JSON text."""
    kwargs: Dict[str, Any] = {
        "ensure_ascii": False,
        "sort_keys": True,
    }
    if compact:
        kwargs["separators"] = (",", ":")
    else:
        kwargs["indent"] = 2
    return json.dumps(contract_snapshot(), **kwargs)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export business-tool risk/profit contracts as JSON."
    )
    parser.add_argument(
        "--output",
        help="Write the JSON snapshot to this path instead of stdout.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON without indentation.",
    )
    args = parser.parse_args()

    content = export_contracts(compact=args.compact)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"{content}\n", encoding="utf-8")
        print(f"Wrote business tool contracts to {output_path}", file=sys.stderr)
    else:
        print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
