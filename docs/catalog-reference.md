# Catalog Reference

The catalog is the authoritative description of *what the agent is allowed to do*. It is a JSON document validated against [`schemas/catalog.schema.json`](../schemas/catalog.schema.json).

## Top-level shape

```json
{
  "name":         "Smart Office Agent Harness",
  "version":     "0.1.0",
  "actions":     { ... },
  "capabilities":{ ... },
  "groups":      { ... },
  "scenarios":   { ... },
  "policies":    { "fuzzy_cutoff": 0.62 }
}
```

| Field | Required | Description |
| --- | --- | --- |
| `name` | no | Human label, shown in Studio. |
| `version` | no | Free-form version string. |
| `actions` | yes | Action vocabulary. |
| `capabilities` | yes | Capabilities the actions apply to. |
| `groups` | no | Named sets of capabilities. |
| `scenarios` | no | Named deterministic sequences. |
| `policies` | no | Catalog-side defaults (only `fuzzy_cutoff` today). |

## Actions

Each action declares natural-language verbs that the router uses to short-circuit the model:

```json
"actions": {
  "turn_on":  { "verbs": ["turn on", "enable", "switch on"] },
  "turn_off": { "verbs": ["turn off", "disable"] }
}
```

| Field | Description |
| --- | --- |
| `verbs` | List of canonical phrases. The router matches inputs against these. |
| `description` | Optional documentation shown in Studio. |

## Capabilities

A capability is *the thing actions act on*.

```json
"capabilities": {
  "Lobby lights": {
    "actions":    ["turn_on", "turn_off", "set"],
    "aliases":    ["entrance lights", "front lobby"],
    "parameters": {
      "level":       { "values": ["low", "medium", "high"] },
      "temperature": { "values": ["warm", "neutral", "cool"] }
    },
    "state": { "status": "inactive", "level": "low", "temperature": "warm" }
  }
}
```

| Field | Required | Description |
| --- | --- | --- |
| `actions` | yes | Subset of the global action list this capability supports. |
| `aliases` | no | Extra names the router and validator will accept. |
| `parameters` | no | Parameter schemas — see below. |
| `state` | no | Initial state seeded into the atomic state store. |
| `description` | no | Documentation. |

### Parameter schema

```json
"parameters": {
  "level":      { "values": ["low", "medium", "high"] },
  "temperature":{ "values": ["warm", "neutral", "cool"] },
  "intensity":  { "min": 0, "max": 100 },
  "ticket_id":  { "pattern": "^T-[0-9]+$" },
  "note":       { "type": "string", "max_length": 1000 }
}
```

| Constraint | Behaviour |
| --- | --- |
| `values` | Enum of allowed strings. Synonyms in the policy map to canonical values. |
| `min` / `max` | Numeric bounds (inclusive). |
| `pattern` | Regex the value must match (full match). |
| `type` | `"string"`, `"number"`, `"boolean"`. |
| `max_length` | Maximum string length. |
| `required` | If true, the validator rejects calls missing this parameter. |

## Groups

```json
"groups": {
  "Public areas": { "members": ["Lobby lights", "Visitor check-in kiosk"] }
}
```

A target named `Public areas` will fan out the call to every member. Useful for "turn on lights in public areas".

## Scenarios

```json
"scenarios": {
  "opening_mode": {
    "description": "Open the office for the day.",
    "steps": [
      { "target": "Front door",   "action": "unlock" },
      { "target": "Public areas", "action": "turn_on" },
      { "target": "Coffee machine", "action": "start" }
    ]
  }
}
```

Scenarios execute atomically (best-effort) and produce a single `scenario` trace plus one `scenario:step` trace per step.

## State

Each capability can declare an initial `state` object. The state store updates it on every `completed` action. Use it to:

- expose status to the agent via `inspect(target)`;
- drive UI;
- back-source for analytics.

## Validation

Run `literal doctor` after every catalog edit. It checks:

- every action verb is unique enough to route deterministically;
- every capability's `actions` reference an existing action;
- every group member is an existing capability;
- every scenario step references a valid `(target, action, parameters)`;
- every parameter schema is well-formed.

## Related

- [Policy Reference](policy-reference.md)
- [Tutorial](tutorial.md)
