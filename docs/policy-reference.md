# Policy Reference

The policy declares *how* decisions are made and *what is forbidden*. It is validated against [`schemas/policy.schema.json`](../schemas/policy.schema.json).

## Top-level shape

```json
{
  "fuzzy_cutoff":   0.62,
  "inspect_verbs":  ["inspect", "status", "show", "check"],
  "scenario_verbs": ["run", "start", "activate", "execute"],
  "synonyms":       { "high": ["max", "maximum", "bright"] },
  "confirmations":  [ ... ],
  "deny":           [ ... ]
}
```

| Field | Required | Description |
| --- | --- | --- |
| `fuzzy_cutoff` | no | Minimum similarity (0..1) for fuzzy target matching. Default `0.62`. |
| `inspect_verbs` | no | Verbs that route to the `inspect` action. |
| `scenario_verbs` | no | Verbs that route to the `scenario` action. |
| `synonyms` | no | Map of canonical value → synonyms. The validator resolves synonyms before checking `values`. |
| `confirmations` | no | Pairs that require an explicit confirmation flag from the caller. |
| `deny` | no | Pairs that are always rejected. |

## `fuzzy_cutoff`

Controls how aggressive the router is when matching target names.

- `1.0` — exact match only.
- `0.7`–`0.8` — strict, suitable for safety-critical domains.
- `0.5`–`0.65` — relaxed, suitable for conversational UIs.

A higher cutoff produces more `ambiguous` routes (the LLM is consulted). A lower cutoff produces more `fast_path` routes (cheaper, but watch for false positives).

## `inspect_verbs` and `scenario_verbs`

```json
"inspect_verbs":  ["status", "show", "what is", "check"],
"scenario_verbs": ["run", "trigger", "execute"]
```

When the router sees `"status lobby lights"` it routes to `inspect("Lobby lights")` without invoking any action verb. Similarly `"run opening mode"` routes to `scenario("opening_mode")`.

## `synonyms`

```json
"synonyms": {
  "high":     ["max", "maximum", "bright"],
  "low":      ["min", "minimum", "dim"],
  "resolved": ["done", "fixed"]
}
```

If a parameter declares `values: ["low", "medium", "high"]`, an agent that emits `"maximum"` is corrected to `"high"` *before* validation. This lets your model speak naturally and your policy stay strict.

## `confirmations`

```json
"confirmations": [
  { "target": "Server room door", "action": "unlock",
    "reason": "Restricted access requires explicit confirmation." }
]
```

When a confirmation matches:

- the call **does not execute**;
- the response is `{ ok: false, outcome: "requires_confirmation", reason: ... }`;
- the trace records the requirement;
- the caller must re-invoke with an explicit confirmation flag (the runtime decides how to surface it — checkbox, second prompt, signed approval, etc.).

This is the right place for "anything that costs money", "anything that pages a human", "anything physical".

## `deny`

```json
"deny": [
  { "target": "Production DB", "action": "drop_table",
    "reason": "Forbidden in this environment." }
]
```

Denied calls **never execute**. The response is `{ ok: false, outcome: "denied", reason: ... }`. The trace is written. There is no way for the agent to bypass this without editing the policy file.

Use `deny` for:

- destructive operations you never want from an agent;
- temporary kill switches during incidents;
- environment-specific bans (e.g., deny in prod, allow in staging).

## Wildcards (planned)

Today both `target` and `action` are exact strings. A future release will add prefix wildcards (`"prod_*"`) and condition guards (`when.state.hour`, `when.params.amount > 10000`). The protocol is designed to extend without breaking changes.

## Composing layers

For a typical production deployment:

1. **Catalog** enforces *shape* (regex, enums, ranges).
2. **Policy `confirmations`** enforces *human-in-the-loop* on impactful actions.
3. **Policy `deny`** enforces *absolute prohibitions*.
4. **Synonyms** keep the agent's language flexible without weakening validation.

## Related

- [Catalog Reference](catalog-reference.md)
- [Use Cases](use-cases.md)
- [Security & Deployment](security.md)
