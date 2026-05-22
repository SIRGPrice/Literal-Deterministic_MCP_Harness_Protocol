"""Validate and smoke-test the advanced Literal examples."""

from __future__ import annotations

from pathlib import Path

from literal import Registry, harness

ROOT = Path(__file__).resolve().parent

EXAMPLES = {
    "hospital-command-center": {
        "checks": [
            ("simulate", ("status ED",), "completed"),
            ("invoke", ("Clinical Authority Boundary", "create_prescription", {"reason": "agent_request"}), "denied"),
            ("invoke", ("Hospital Incident Command", "open_incident_channel", {"team": "operations", "severity": "critical"}), "confirmation_required"),
        ]
    },
    "fintech-risk-ops": {
        "checks": [
            ("simulate", ("status AML",), "completed"),
            ("invoke", ("Treasury Vault", "wire_funds", {"currency": "USD", "amount": 250000, "destination": "settlement_partner", "reason": "settlement"}), "confirmation_required"),
            ("invoke", ("EU Card Ledger", "delete_ledger_entry", {"tenant": "acme_eu", "reason": "manual_review"}), "denied"),
        ]
    },
    "critical-infrastructure-grid": {
        "checks": [
            ("simulate", ("telemetry SW17",), "completed"),
            ("invoke", ("Breaker SW-17", "open_breaker", {"reason": "fault_isolation", "priority": "critical"}), "confirmation_required"),
            ("invoke", ("Breaker SW-17", "disable_protection", {"reason": "manual_review", "priority": "critical"}), "denied"),
        ]
    },
}


def trace_outcome(result: dict) -> str:
    trace = result.get("trace") or {}
    return str(trace.get("outcome", "unknown"))


def main() -> int:
    for name, config in EXAMPLES.items():
        folder = ROOT / name
        catalog = folder / "literal.catalog.json"
        policy = folder / "literal.policy.json"
        registry = Registry.from_paths(catalog, policy)
        print(f"OK {name}: {len(registry.actions)} actions, {len(registry.capabilities)} capabilities, {len(registry.groups)} groups, {len(registry.scenarios)} scenarios")

        example_harness = harness(catalog, policy)
        for method, args, expected in config["checks"]:
            result = getattr(example_harness, method)(*args)
            outcome = trace_outcome(result)
            status = "OK" if outcome == expected else "FAIL"
            print(f"  {status} {method} -> {outcome} (expected {expected})")
            if outcome != expected:
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
