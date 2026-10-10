#!/usr/bin/env python
"""Zero-dependency preflight check (spec section 18/33 GATE 1).

Stub for this session: deployment is out of scope (see
docs/DEPLOYMENT.md). This script only performs static, offline checks that
do not require a running node or network access, so it can be run safely
right now. A follow-on session that performs the live deployment should
extend this with the schema/ABI checks from master-spec section 19.
"""

import ast
import sys
from pathlib import Path

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "contracts" / "handover_protocol.py"

FORBIDDEN_CALLS = {
    ("time", "time"),
    ("random", "random"),
    ("requests", "get"),
    ("requests", "post"),
    ("os", "urandom"),
}


def check_forbidden_nondeterminism(tree: ast.Module) -> list[str]:
    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                pair = (node.func.value.id, node.func.attr)
                if pair in FORBIDDEN_CALLS:
                    problems.append(f"line {node.lineno}: forbidden call {pair[0]}.{pair[1]}(...)")
    return problems


def check_header(text: str) -> list[str]:
    problems = []
    header = "\n".join(text.splitlines()[:3])
    if '"Depends"' not in header:
        problems.append("missing GenVM dependency header comment in the contract header")
    return problems


def main() -> int:
    if not CONTRACT_PATH.exists():
        print(f"FAIL: contract not found at {CONTRACT_PATH}")
        return 1

    text = CONTRACT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(CONTRACT_PATH))

    problems = check_header(text) + check_forbidden_nondeterminism(tree)

    if problems:
        print("PREFLIGHT: FAIL")
        for p in problems:
            print(f"  - {p}")
        return 1

    print("PREFLIGHT: PASS (static checks only; no live schema/ABI check performed)")
    print("  - header dependency comment present")
    print("  - no forbidden nondeterministic stdlib calls found")
    print("  NOTE: full GenVM lint/schema validation requires a running node")
    print("  (localnet simulator or Studionet) and was not run this session.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
