# Use Cases

Literal is most useful when **wrong tool calls are expensive** — money, safety, data, or trust. Below are concrete scenarios, the problem each one solves, and how Literal helps.

For each use case we list:

- **Problem** — what hurts today.
- **Literal answer** — which Literal mechanism addresses it.
- **Catalog/policy sketch** — minimal example.

---

## 1. Support-desk agent

**Problem.** An LLM customer-support agent occasionally replies to the wrong ticket, sends a half-finished draft, or escalates to the wrong queue.

**Literal answer.**
- Catalog enforces ticket-ID shape (`^T-[0-9]+$`).
- Policy denies `reply` until QA is enabled.
- Policy requires confirmation on `escalate`.
- Traces give you a full reply-by-reply audit log.

```json
{
  "confirmations": [{ "target": "Ticket", "action": "escalate", "reason": "Notifies humans." }],
  "deny":          [{ "target": "Ticket", "action": "reply",    "reason": "Awaiting QA." }]
}
```

---

## 2. Internal IT / DevOps agent

**Problem.** Ops agents that can restart services, scale clusters, or rotate credentials are catastrophic when wrong.

**Literal answer.**
- Group capabilities by environment (`prod_*`, `staging_*`).
- Deny destructive verbs in `prod_*` entirely; require confirmation in `staging_*`.
- Scenario `safe_restart` codifies the *correct* sequence so the LLM cannot improvise.

```json
{
  "deny": [
    { "target": "prod_database", "action": "drop_table" },
    { "target": "prod_cluster",  "action": "scale_down_to_zero" }
  ],
  "confirmations": [
    { "target": "prod_service", "action": "restart", "reason": "Triggers paging." }
  ]
}
```

---

## 3. Industrial / IoT / building automation

**Problem.** Physical actuators (doors, locks, valves, motors) cannot be "undone" by a retry. A misrouted unlock can have legal consequences.

**Literal answer.**
- Strict capability aliases prevent fuzzy matches on safety-critical assets.
- Confirmations on every actuator with physical risk.
- Atomic state store records the canonical position of each device.
- Decision traces map directly to compliance audits.

```json
{
  "confirmations": [
    { "target": "Server room door", "action": "unlock", "reason": "Restricted access." },
    { "target": "Valve V-12",       "action": "open",   "reason": "Industrial safety." }
  ],
  "deny": [
    { "target": "Emergency shutoff", "action": "disable" }
  ]
}
```

---

## 4. Financial / billing operations

**Problem.** Agents performing refunds, fee waivers, or account credits can leak money under prompt-injection or misclassification.

**Literal answer.**
- Parameter `max` enforces a hard refund ceiling per call.
- Confirmations on any amount above a threshold (modelled via a dedicated `large_refund` action).
- Deny on currency mismatches or production account IDs the agent shouldn't touch.

```json
{
  "capabilities": {
    "Refund": {
      "actions": ["small_refund", "large_refund"],
      "parameters": {
        "amount":   { "min": 0, "max": 500 },
        "currency": { "values": ["EUR", "USD"] }
      }
    }
  },
  "confirmations": [
    { "target": "Refund", "action": "large_refund", "reason": "Above auto-approval threshold." }
  ]
}
```

---

## 5. Healthcare workflow assistant

**Problem.** Clinical assistants that schedule, message, or order tests must never act on stale or ambiguous identifiers.

**Literal answer.**
- Patient IDs constrained by `pattern`.
- Deny on prescribing actions until clinician sign-off.
- Inspect verbs map to read-only views (the model can *see* the chart but not change it).

```json
{
  "actions": {
    "inspect_chart": { "verbs": ["show chart", "open chart"] }
  },
  "deny": [
    { "target": "Prescription", "action": "create" }
  ]
}
```

---

## 6. Multi-tenant SaaS copilot

**Problem.** A single agent runtime serves many customers; their tools must never leak across tenants.

**Literal answer.**
- One catalog per tenant, loaded by the runtime per request.
- Same code path, isolated by configuration — no per-customer branching.
- Per-tenant traces ship to per-tenant log sinks.

```python
from literal import harness

def get_harness(tenant_id: str):
    return harness(f"tenants/{tenant_id}/catalog.json",
                   f"tenants/{tenant_id}/policy.json",
                   state=f"tenants/{tenant_id}/state.json",
                   traces=f"tenants/{tenant_id}/traces.jsonl")
```

---

## 7. Prompt-injection hardening

**Problem.** A malicious document persuades the agent to call `delete_all_files()`.

**Literal answer.**
- The model can only emit calls that match the catalog. There is no `delete_all_files` action to call.
- Even if the model produces `delete` on `Customer`, the validator rejects unless `Customer` whitelists `delete`.
- A `deny` entry adds a second, explicit barrier you can demonstrate to security review.

This is the strongest qualitative benefit: **the agent's blast radius equals the catalog**, no more.

---

## 8. Cost & latency reduction

**Problem.** Sending the entire tool schema in every prompt is expensive and slow.

**Literal answer.**
- The prompt builder emits a compact vocabulary block (a few hundred tokens) instead of the full schema (thousands).
- Stable prompts cache better at the model provider.
- The router resolves a large fraction of inputs without the model at all — that traffic is free.

Quantitative effect varies by domain but the qualitative pattern is consistent: lower token cost, lower p95 latency, fewer surprise tool calls.

---

## 9. Regulatory / audit readiness

**Problem.** An auditor asks: *"show me every action your agent took on customer 47812 last month and why."*

**Literal answer.**
- JSONL traces are append-only, timestamped, structured.
- Each trace contains the exact input, the route, the matches, the parameters, the outcome, and the policy reason if denied.
- You can replay traces deterministically against the same catalog/policy to regenerate the decision.

---

## 10. Cross-team policy ownership

**Problem.** Security wants to gate agent behaviour; engineering wants to ship.

**Literal answer.**
- Catalog (engineering owns) is decoupled from policy (security owns).
- Policy changes do not require code deploys.
- Studio gives security a UI to review, simulate, and ship policy without touching Python.

---

## Putting it together

A mature Literal deployment usually layers all of the above:

1. Engineering ships a **catalog** with strict parameter constraints.
2. Security owns a **policy** with denies, confirmations, and synonyms.
3. The runtime team enables **traces shipping** to SIEM (Splunk, Datadog, Elastic).
4. Studio is exposed read-only to support and audit functions.

That is the day-in-the-life Literal is designed for.
