# Critical Infrastructure Grid

This example models a grid-operations harness for demand response, microgrid islanding, critical-load protection, and physical breaker control.

## What it demonstrates

- A very strict `fuzzy_cutoff` (`0.82`) for physical infrastructure.
- Physical actuators (`Breaker SW-17`) behind confirmation gates.
- Deny rules for protection bypass and critical hospital load shedding.
- Groups that coordinate batteries, feeders, breakers, solar, and EV load.
- Scenarios that prepare complex runbooks while making the risky steps explicit.

## Try it

```bash
python -m literal.cli --catalog examples/advanced/critical-infrastructure-grid/literal.catalog.json --policy examples/advanced/critical-infrastructure-grid/literal.policy.json doctor
```

Useful simulations from Python:

```python
from literal import harness

h = harness(
    "examples/advanced/critical-infrastructure-grid/literal.catalog.json",
    "examples/advanced/critical-infrastructure-grid/literal.policy.json",
)

print(h.simulate("telemetry SW17"))
print(h.simulate("run peak response"))
print(h.invoke("Breaker SW-17", "open_breaker", {"reason": "fault_isolation", "priority": "critical"}))
print(h.invoke("Breaker SW-17", "disable_protection", {"reason": "manual_review", "priority": "critical"}))
```

## Why it is complex

Grid operations expose the hardest version of agent safety: physical operations, live state, critical loads, expensive mistakes, and strict audit requirements.

Literal's value here is the separation between orchestration and authority:

- the agent can prepare and explain a runbook;
- policy blocks forbidden operations;
- confirmation gates stop physical actuator changes;
- traces show exactly why a breaker, islanding, or load command did or did not run.
