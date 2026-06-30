#!/usr/bin/env python3
"""Run MCP equivalence checks (native @tool vs MCP wrapper)."""

from __future__ import annotations

import json
import sys

from talentscreen.mcp.equivalence import run_equivalence_checks


def main() -> int:
    report = run_equivalence_checks()
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        print("FAIL: MCP wrappers diverged from native @tool", file=sys.stderr)
        return 1
    print("PASS: MCP wrappers match native @tool")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
