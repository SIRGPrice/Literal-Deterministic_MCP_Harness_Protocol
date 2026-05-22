# Literal Protocol Specification

> Status: Draft. Versioned independently of the Python reference implementation.
> Protocol version: **0.2**.

This document defines the wire-level contract a runtime must implement to be **Literal-compatible**. It is the basis for ports to other languages (TypeScript/JavaScript, Rust, Kotlin, Go) and for a future cross-implementation conformance test suite.

The Python package in this repository is the **reference implementation**.

## 1. Terminology

- **Capability** — an addressable thing the agent can act on.
- **Action** — a verb supported by one or more capabilities.
- **Catalog** — a JSON document declaring actions, capabilities, groups, scenarios.
- **Policy** — a JSON document declaring routing tuning and guardrails (deny, confirmations, synonyms).
- **Route** — the result of resolving an input to a `(target, action, parameters)` tuple.
- **Outcome** — the terminal classification of a call.
- **Trace** — an immutable record of one decision.

## 2. File formats

### 2.1 Catalog

Validated by `schemas/catalog.schema.json`. Top-level keys:

| Key | Type | Required |
| --- | --- | --- |
| `name` | string | no |
| `version` | string | no |
| `actions` | object<string, ActionDef> | yes |
| `capabilities` | object<string, CapabilityDef> | yes |
| `groups` | object<string, GroupDef> | no |
| `scenarios` | object<string, ScenarioDef> | no |
| `policies` | object | no (catalog-side hints) |

`ActionDef`:
```ts
{ verbs: string[], description?: string }
```

`CapabilityDef`:
```ts
{
  actions: string[],
  aliases?: string[],
  parameters?: { [name: string]: ParamSchema },
  state?: object,
  description?: string
}
```

`ParamSchema`:
```ts
{
  type?: "string" | "number" | "boolean",
  values?: string[],
  min?: number,
  max?: number,
  pattern?: string,           // RE2-compatible regex; full match
  max_length?: number,
  required?: boolean
}
```

`GroupDef`:
```ts
{ members: string[] }
```

`ScenarioDef`:
```ts
{
  description?: string,
  steps: { target: string, action: string, parameters?: object }[]
}
```

### 2.2 Policy

Validated by `schemas/policy.schema.json`.

```ts
{
  fuzzy_cutoff?: number,            // 0..1, default 0.62
  inspect_verbs?: string[],
  scenario_verbs?: string[],
  synonyms?: { [canonical: string]: string[] },
  confirmations?: { target: string, action: string, reason?: string }[],
  deny?:          { target: string, action: string, reason?: string }[]
}
```

## 3. Routing semantics

Given a free-text input, a compliant runtime MUST resolve in this order:

1. **Inspect verbs.** If the input begins with or contains an `inspect_verb`, route to `inspect(target)` and stop.
2. **Scenario verbs.** If the input matches a `scenario_verb` followed by a scenario name (or alias), route to `scenario(name)` and stop.
3. **Exact verb match.** If the input contains a declared action verb and exactly one capability accepts that action, route deterministically.
4. **Fuzzy match.** Score capability names + aliases against the input remainder. If the top match has score ≥ `fuzzy_cutoff` and is uniquely best, route deterministically.
5. **Ambiguous.** Otherwise return an `AmbiguousRoute` with all candidate matches. A runtime MAY invoke a model at this stage; the model's output MUST flow back through validation.

Synonyms from the policy MUST be applied to parameter values **before** validation.

## 4. Validation semantics

Given `(target, action, parameters, confirmed?)`:

1. **Catalog check.** If `target` does not exist (after group expansion) or does not accept `action`, outcome is `invalid`.
2. **Deny.** If `(target, action)` matches any policy `deny` entry, outcome is `denied`. No further steps run.
3. **Parameter check.** For each declared parameter:
   - `required: true` and missing → `invalid`.
   - `type` mismatch → `invalid`.
   - `values` set and value not in (set ∪ resolved synonyms) → `invalid`.
   - `pattern` set and value does not full-match → `invalid`.
   - `min`/`max` set and value out of range → `invalid`.
   - `max_length` set and string longer → `invalid`.
4. **Confirmation.** If `(target, action)` matches any policy `confirmations` entry **and** `confirmed != true`, outcome is `requires_confirmation`. Execution MUST NOT occur.
5. **Execute.** Handler is invoked. If it raises, outcome is `error`. Otherwise outcome is `completed`.

After execution, the runtime MUST update capability state (if the handler returned a state delta) and write exactly one trace.

## 5. Outcomes

A compliant runtime MUST produce one of these terminal outcomes per call:

| Outcome | Meaning |
| --- | --- |
| `completed` | Handler ran successfully. |
| `denied` | Policy `deny` matched. |
| `invalid` | Catalog or parameter check failed. |
| `requires_confirmation` | Policy `confirmations` matched and `confirmed` was not set. |
| `error` | Handler raised. |
| `ambiguous` | (Routing-only) returned by `simulate` when no model is configured to break ties. |

## 6. Trace record

Each decision MUST produce one JSON object appended as a single line (no internal newlines) to the trace sink.

```ts
{
  id:        string,        // monotonically generated id
  ts:        string,        // ISO 8601 UTC
  input:     string,        // raw input (may be empty for structured invokes)
  route:    "fast_path" | "ambiguous" | "model" | "direct" | "scenario" | "inspect",
  target:    string | null,
  action:    string | null,
  parameters: object,
  outcome:   "completed" | "denied" | "invalid" | "requires_confirmation" | "error" | "ambiguous",
  reason:    string | null,
  matches?:  { target: string, score: number }[],
  state_delta?: object,
  error?:    { message: string, type?: string }
}
```

Scenarios produce one parent `scenario` trace plus one child per step.

## 7. MCP adapter contract

A Literal-compatible MCP server MUST expose:

- Tool `invoke(target: string, action: string, parameters_json: string)`.
- Tool `inspect(target: string)`.
- Tool `scenario(name: string)`.
- Resource `literal://catalog` returning the active catalog as JSON.
- Resource `literal://traces` returning recent traces as JSONL or JSON array.

`parameters_json` is a JSON-encoded string for client compatibility. The server is responsible for decoding it before validation.

## 8. HTTP adapter contract

A Literal-compatible HTTP server MUST expose:

- `GET  /api/health` → `{ ok: true, version: string }`.
- `GET  /api/catalog` → catalog JSON.
- `GET  /api/policies` → policy JSON.
- `POST /api/simulate { text }` → decision response.
- `POST /api/invoke { target, action, parameters?, confirmed? }` → decision response.
- `POST /api/scenario { name }` → decision response.
- `GET  /api/traces?limit&outcome&target` → `{ traces: Trace[] }`.

Decision responses MUST include at minimum: `ok`, `outcome`, `route`, `target`, `action`, `parameters`, `trace_id`. Non-`completed` outcomes MUST include a `reason`.

## 9. Versioning

The protocol version is independent of the Python package version. Breaking changes to file formats, outcomes, trace fields, or MCP/HTTP contracts increment the minor version (0.x → 0.y). The reference implementation is `Literal/<package-version>`; the protocol version is reported as `protocol: "0.2"`.

## 10. Conformance

A future test suite will provide:

- catalog/policy fixtures with declared expected outcomes for a corpus of inputs;
- HTTP and MCP test harnesses that drive any implementation;
- a trace-replay tool that checks deterministic reproduction.

Ports that pass the suite may use the **Literal-compatible** designation.

## 11. Open questions (not in this version)

- Wildcards and prefix matching in policy entries.
- Conditional guards (`when.state.*`, `when.params.*`).
- Signed catalogs and signed traces.
- Streaming / async handlers.

These are tracked for protocol v0.3+.

## License

The protocol specification is published under the same license as the reference implementation. See [LICENSE](../LICENSE).
