# Advanced Examples

These examples are intentionally large. They are not starter templates; they are stress tests that show how far Literal can go when a team treats the protocol as a governance layer for real agent operations.

Each example contains:

- `literal.catalog.json` - the full capability catalog.
- `literal.policy.json` - the governance policy.
- `README.md` - what the example demonstrates and what to try.

## Scenarios

| Example | Domain | What it demonstrates |
| --- | --- | --- |
| [hospital-command-center](hospital-command-center/README.md) | Hospital operations | Multi-unit coordination, clinical safety boundaries, incident scenarios, escalation gates. |
| [fintech-risk-ops](fintech-risk-ops/README.md) | Financial risk operations | Multi-tenant rails, fraud queues, refund limits, treasury gates, audit evidence. |
| [critical-infrastructure-grid](critical-infrastructure-grid/README.md) | Energy / grid operations | Physical actuator control, microgrid islanding, demand response, breaker confirmations. |

## Validate all examples

From the repository root:

```bash
python examples/advanced/run.py
```

Or run one manually:

```bash
python -m literal.cli --catalog examples/advanced/hospital-command-center/literal.catalog.json --policy examples/advanced/hospital-command-center/literal.policy.json doctor
```

## Why these are useful

The core point is not that an LLM can do more. The point is that the protocol can absorb complex operating domains while keeping these invariants:

1. The agent only sees a bounded vocabulary.
2. Every high-risk operation goes through policy.
3. Every decision becomes a trace.
4. Domain owners can change rules without changing runtime code.

Read [Advanced Examples](../../docs/advanced-examples.md) for the narrative walkthrough.
