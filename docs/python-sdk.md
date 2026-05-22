# Python SDK

The Python package exposes a short, ergonomic surface plus the underlying classes.

## Install

```bash
python -m pip install literal           # core
python -m pip install 'literal[mcp]'    # core + MCP stdio adapter
python -m pip install 'literal[dev]'    # + pytest, pytest-asyncio
```

## The fast path: `harness()`

```python
from literal import harness

h = harness("literal.catalog.json", "literal.policy.json")

print(h.simulate("turn on lobby lights"))
print(h.inspect("Lobby lights"))
print(h.scenario("opening_mode"))
```

Signature:

```python
harness(
    catalog: str | Path = "literal.catalog.json",
    policy:  str | Path | None = "literal.policy.json",
    *,
    state:   str | Path | None = None,
    traces:  str | Path | None = None,
    handler: Handler | None = None,
) -> Harness
```

| Argument | Purpose |
| --- | --- |
| `catalog` | Path to catalog JSON. |
| `policy` | Path to policy JSON. Pass `None` to run without a policy file. |
| `state` | Path to atomic state file. Defaults to in-memory. |
| `traces` | Path to JSONL traces file. Defaults to in-memory. |
| `handler` | Callable invoked for each `completed` action — your real tool implementation. |

## Custom tool execution

By default Literal performs the routing, validation, and state-tracking but does **not** call your real tools. Pass a `handler` to wire execution:

```python
from literal import harness

def execute(target: str, action: str, parameters: dict):
    if target == "Lobby lights" and action == "turn_on":
        my_iot_client.lights("lobby").on(**parameters)
        return {"status": "ok"}
    raise NotImplementedError(f"{target}.{action}")

h = harness("literal.catalog.json", "literal.policy.json", handler=execute)
print(h.simulate("turn on lobby lights"))
```

The handler runs only for calls the validator allowed. Denied, invalid, or unconfirmed calls never reach it.

## Lower-level classes

```python
from literal import Harness, Registry

registry = Registry.from_paths("literal.catalog.json", "literal.policy.json")
h = Harness(registry)
```

| Symbol | Role |
| --- | --- |
| `Harness` | Orchestrator. Runs router → validator → handler → state → trace. |
| `Registry` | Parsed catalog + policy. |
| `Router` | Deterministic intent resolver. |
| `Validator` | Policy enforcement. |
| `StateStore` | Atomic per-capability state. |
| `TraceStore` | JSONL trace log. |
| `Trace` | One decision record. |
| `DirectRoute`, `AmbiguousRoute` | Router result types. |
| `ValidationResult` | Validator result. |

Legacy long names — `ToolHarness`, `CapabilityRegistry`, `PolicyValidator`, `DeterministicRouter`, `AtomicStateStore`, `DecisionTrace` — remain importable as aliases for backward compatibility.

## Operations

### `simulate(text: str) -> dict`

Run the full pipeline (router → optionally model → validator → handler → trace) on a free-text input.

### `invoke(target, action, parameters=None, *, input_text="") -> dict`

Run only the validator + handler + trace path. Use this when your agent already produced a structured call.

### `inspect(target: str) -> dict`

Read the current state of a capability. Routed automatically when the input matches an `inspect_verb`.

### `scenario(name: str) -> dict`

Execute a named scenario. Each step is validated and traced individually.

### `recent_traces(limit: int = 50) -> list[Trace]`

Return the most recent traces from the trace store.

## Confirmations

When a call hits a `confirmations` policy:

```python
result = h.invoke("Server room door", "unlock")
# -> { "ok": False, "outcome": "requires_confirmation", "reason": "..." }
```

Resend with the explicit flag once your application has obtained confirmation:

```python
result = h.invoke("Server room door", "unlock", confirmed=True)
```

## Errors

The SDK raises only for programmer errors (bad paths, malformed JSON). Decision outcomes — denied, invalid, requires_confirmation, error — are returned as structured dicts so you can always inspect them and log them uniformly.

## Related

- [Tutorial](tutorial.md)
- [HTTP API](http-api.md)
- [MCP Integration](mcp-integration.md)
