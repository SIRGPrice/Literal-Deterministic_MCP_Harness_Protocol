# Fintech Risk Operations

This example models a fintech risk operations layer across card, ACH, AML, treasury, chargeback, and tenant-control workflows.

## What it demonstrates

- Multi-tenant catalogs with tenant IDs constrained as enum values.
- Separate payment rails with shared action vocabulary.
- Refund ceilings via `range` constraints.
- Confirmation gates on account freezes, large refunds, wires, and key rotation.
- Append-only ledger enforcement through explicit deny rules.
- Scenarios that prepare evidence packs without moving funds autonomously.

## Try it

```bash
python -m literal.cli --catalog examples/advanced/fintech-risk-ops/literal.catalog.json --policy examples/advanced/fintech-risk-ops/literal.policy.json doctor
```

Useful simulations from Python:

```python
from literal import harness

h = harness(
    "examples/advanced/fintech-risk-ops/literal.catalog.json",
    "examples/advanced/fintech-risk-ops/literal.policy.json",
)

print(h.simulate("status AML"))
print(h.simulate("run fraud lockdown"))
print(h.invoke("Treasury Vault", "wire_funds", {"currency": "USD", "amount": 250000, "destination": "settlement_partner", "reason": "settlement"}))
print(h.invoke("EU Card Ledger", "delete_ledger_entry", {"tenant": "acme_eu", "reason": "manual_review"}))
```

## Why it is complex

Fintech agents need to speak across rails, tenants, compliance queues, refunds, credentials, and treasury without being allowed to invent money movement. Literal makes that tractable because each surface is separate:

- catalog = allowed operational vocabulary;
- policy = legal and risk gates;
- trace = audit evidence;
- scenarios = deterministic runbooks that prepare evidence without crossing into forbidden execution.
