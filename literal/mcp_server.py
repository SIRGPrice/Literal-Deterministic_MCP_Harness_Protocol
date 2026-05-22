"""Optional MCP stdio adapter for Literal — Deterministic MCP Harness Protocol."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .harness import Harness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Literal as an MCP stdio server")
    parser.add_argument("--catalog", default="literal.catalog.json")
    parser.add_argument("--policy", default="literal.policy.json")
    parser.add_argument("--state", default=".literal/state.json")
    parser.add_argument("--traces", default=".literal/traces.jsonl")
    args = parser.parse_args(argv)

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as error:
        raise SystemExit(
            "The optional 'mcp' dependency is not installed. "
            "Install with: pip install 'literal[mcp]'"
        ) from error

    h = Harness.from_paths(
        catalog_path=Path(args.catalog),
        policy_path=Path(args.policy),
        state_path=Path(args.state),
        trace_path=Path(args.traces),
    )

    mcp = FastMCP(
        "Literal",
        instructions=(
            "Literal — Deterministic MCP Harness Protocol. Use invoke for governed execution, "
            "inspect for current state, and scenario for repeatable multi-step flows."
        ),
    )

    @mcp.tool()
    def invoke(target: str, action: str, parameters_json: str = "{}") -> str:
        """Validate and execute a governed tool call."""
        try:
            parameters: dict[str, Any] = json.loads(parameters_json or "{}")
        except json.JSONDecodeError:
            parameters = {}
        return json.dumps(h.invoke(target, action, parameters), ensure_ascii=False)

    @mcp.tool()
    def inspect(target: str = "") -> str:
        """Inspect the current state for one target or the whole harness."""
        return json.dumps(h.inspect(target or None), ensure_ascii=False)

    @mcp.tool()
    def scenario(name: str) -> str:
        """Run a predefined deterministic scenario."""
        return json.dumps(h.scenario(name), ensure_ascii=False)

    @mcp.resource("literal://catalog")
    def catalog() -> str:
        return json.dumps(h.catalog(), ensure_ascii=False, indent=2)

    @mcp.resource("literal://traces")
    def traces() -> str:
        return json.dumps(h.trace_list(limit=100), ensure_ascii=False, indent=2)

    mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
