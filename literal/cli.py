"""Command line interface for Literal — Deterministic MCP Harness Protocol."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from importlib.resources import files
from pathlib import Path
from typing import Any

from .registry import CapabilityRegistry, CatalogError
from .server import StudioServerConfig, run_studio_server

DEFAULT_CATALOG = "literal.catalog.json"
DEFAULT_POLICY = "literal.policy.json"
DEFAULT_STATE = ".literal/state.json"
DEFAULT_TRACES = ".literal/traces.jsonl"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="literal", description="Literal — Deterministic MCP Harness Protocol")
    parser.add_argument("--catalog", default=DEFAULT_CATALOG, help="Catalog JSON path")
    parser.add_argument("--policy", default=DEFAULT_POLICY, help="Policy JSON path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a local harness configuration")
    init_parser.add_argument("--template", default="smart-office", choices=["smart-office"], help="Starter template")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing files")

    dev_parser = subparsers.add_parser("dev", help="Run local API and built Literal Studio")
    dev_parser.add_argument("--host", default="127.0.0.1")
    dev_parser.add_argument("--port", type=int, default=8787)
    dev_parser.add_argument("--state", default=DEFAULT_STATE)
    dev_parser.add_argument("--traces", default=DEFAULT_TRACES)
    dev_parser.add_argument("--static-dir", default="apps/studio/dist")
    dev_parser.add_argument("--no-browser", action="store_true")

    subparsers.add_parser("doctor", help="Validate the local harness configuration")

    add_tool_parser = subparsers.add_parser("add-tool", help="Add a capability to the catalog")
    add_tool_parser.add_argument("name", help="Capability name")
    add_tool_parser.add_argument("--action", action="append", default=[], help="Allowed action; can be repeated")
    add_tool_parser.add_argument("--alias", action="append", default=[], help="Alias; can be repeated")
    add_tool_parser.add_argument("--kind", default="capability")

    export_parser = subparsers.add_parser("export", help="Print integration snippets")
    export_parser.add_argument("--format", choices=["all", "mcp", "python", "http"], default="all")

    args = parser.parse_args(argv)

    if args.command == "init":
        return _cmd_init(args)
    if args.command == "dev":
        return _cmd_dev(args)
    if args.command == "doctor":
        return _cmd_doctor(args)
    if args.command == "add-tool":
        return _cmd_add_tool(args)
    if args.command == "export":
        return _cmd_export(args)
    parser.print_help()
    return 2


def _cmd_init(args: argparse.Namespace) -> int:
    catalog_path = Path(args.catalog)
    policy_path = Path(args.policy)
    _copy_template("catalog.smart-office.json", catalog_path, force=args.force)
    _copy_template("policy.default.json", policy_path, force=args.force)
    Path(".literal").mkdir(exist_ok=True)
    print(f"Created {catalog_path}")
    print(f"Created {policy_path}")
    print("Next: literal doctor && literal dev")
    return 0


def _cmd_dev(args: argparse.Namespace) -> int:
    catalog_path = Path(args.catalog)
    policy_path = Path(args.policy)
    if not catalog_path.exists() or not policy_path.exists():
        print("No local configuration found; creating smart-office template first.")
        _copy_template("catalog.smart-office.json", catalog_path, force=False)
        _copy_template("policy.default.json", policy_path, force=False)
    config = StudioServerConfig(
        catalog_path=catalog_path,
        policy_path=policy_path,
        state_path=Path(args.state),
        trace_path=Path(args.traces),
        static_dir=Path(args.static_dir),
    )
    run_studio_server(config=config, host=args.host, port=args.port, open_browser=not args.no_browser)
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    catalog_path = Path(args.catalog)
    policy_path = Path(args.policy)
    if not catalog_path.exists():
        print(f"Missing catalog: {catalog_path}")
        return 1
    if not policy_path.exists():
        print(f"Missing policy: {policy_path}")
        return 1
    try:
        registry = CapabilityRegistry.from_paths(catalog_path, policy_path)
    except (CatalogError, json.JSONDecodeError, OSError) as error:
        print(f"Configuration invalid: {error}")
        return 1
    print("Configuration OK")
    print(f"Catalog: {registry.name} ({registry.version})")
    print(f"Actions: {len(registry.actions)}")
    print(f"Capabilities: {len(registry.capabilities)}")
    print(f"Groups: {len(registry.groups)}")
    print(f"Scenarios: {len(registry.scenarios)}")
    return 0


def _cmd_add_tool(args: argparse.Namespace) -> int:
    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        print(f"Missing catalog: {catalog_path}. Run literal init first.")
        return 1
    catalog = _read_json(catalog_path)
    actions = args.action or list(catalog.get("actions", {}).keys())[:1]
    if not actions:
        print("No actions available. Add actions to the catalog first.")
        return 1
    catalog.setdefault("capabilities", {})[args.name] = {
        "description": "New capability added from CLI.",
        "kind": args.kind,
        "aliases": args.alias,
        "actions": actions,
        "parameters": {},
        "state": {"status": "inactive"},
    }
    _write_json(catalog_path, catalog)
    print(f"Added capability '{args.name}' to {catalog_path}")
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    catalog = str(Path(args.catalog))
    policy = str(Path(args.policy))
    snippets = {
        "mcp": json.dumps(
            {
                "command": "python",
                "args": ["-m", "literal.mcp_server", "--catalog", catalog, "--policy", policy],
            },
            indent=2,
        ),
        "python": (
            "from literal import harness\n\n"
            f"h = harness({catalog!r}, {policy!r})\n"
            "print(h.simulate('turn on lobby lights'))\n"
        ),
        "http": (
            "curl -X POST http://localhost:8787/api/simulate "
            "-H \"Content-Type: application/json\" "
            "-d '{\"text\":\"turn on lobby lights\"}'"
        ),
    }
    if args.format == "all":
        for name, snippet in snippets.items():
            print(f"\n## {name}\n{snippet}")
    else:
        print(snippets[args.format])
    return 0


def _copy_template(name: str, destination: Path, *, force: bool) -> None:
    if destination.exists() and not force:
        print(f"Exists, keeping: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    source = files("literal").joinpath("templates", name)
    with source.open("rb") as source_handle:
        with open(destination, "wb") as destination_handle:
            shutil.copyfileobj(source_handle, destination_handle)


def _read_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as file_handle:
        return json.load(file_handle)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, indent=2, ensure_ascii=False)
    temp_path.replace(path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
