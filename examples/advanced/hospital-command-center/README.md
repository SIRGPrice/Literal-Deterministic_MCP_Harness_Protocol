# Hospital Command Center

This example models a hospital operations command center. It is not a clinical decision engine; it deliberately separates operational coordination from clinical authority.

## What it demonstrates

- A high `fuzzy_cutoff` (`0.78`) for safety-critical routing.
- Explicit safety boundary capability (`Clinical Authority Boundary`) with denied clinical actions.
- Multi-unit groups: `Critical Care Surge Stack` and `Infection Control Stack`.
- Long deterministic scenarios for mass casualty, infectious surge, and imaging backlog recovery.
- Confirmation gates on incident command and cross-unit lockdown.

## Try it

```bash
python -m literal.cli --catalog examples/advanced/hospital-command-center/literal.catalog.json --policy examples/advanced/hospital-command-center/literal.policy.json doctor
```

Useful simulations from Python:

```python
from literal import harness

h = harness(
    "examples/advanced/hospital-command-center/literal.catalog.json",
    "examples/advanced/hospital-command-center/literal.policy.json",
)

print(h.simulate("status ED"))
print(h.simulate("activate MCI intake"))
print(h.invoke("Clinical Authority Boundary", "create_prescription", {"reason": "agent_request"}))
print(h.invoke("Hospital Incident Command", "open_incident_channel", {"team": "operations", "severity": "critical"}))
```

## Why it is complex

A plain agent can be prompted to "coordinate a hospital incident", but it has no durable boundary between logistics and medicine. Literal makes that boundary explicit:

- operational units can be inspected, routed, reserved, and put into modes;
- clinical authority actions exist only so the policy can deny them audibly;
- scenario steps are deterministic, observable, and replayable;
- every escalation becomes a trace that an incident review board can inspect.
