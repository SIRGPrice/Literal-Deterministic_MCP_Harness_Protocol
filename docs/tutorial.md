# Step-by-Step Tutorial

In this tutorial you will model a tiny but realistic domain from scratch — an internal **support-desk agent** that can look up tickets, change their status, and reply to customers — and you will see every Literal layer at work.

By the end you will know:

- how to design a catalog,
- how to write a policy that protects you from agent mistakes,
- how to read a decision trace,
- how to wire an LLM-based agent on top of the harness via MCP.

The whole tutorial takes about 30 minutes. It does not require an API key.

---

## Step 1 — Bootstrap an empty project

```bash
mkdir support-desk && cd support-desk
python -m pip install 'literal[mcp]'
literal init --force
```

Open the generated `literal.catalog.json` in your editor. We will replace it.

## Step 2 — Define your actions

Actions are the verbs your tools accept. In a support-desk you typically have:

```json
{
  "actions": {
    "lookup": {
      "verbs": ["look up", "find", "show", "open"]
    },
    "set_status": {
      "verbs": ["set status", "change status", "mark"]
    },
    "reply": {
      "verbs": ["reply", "respond", "answer"]
    },
    "escalate": {
      "verbs": ["escalate", "hand off", "transfer"]
    }
  }
}
```

The `verbs` list is what the **deterministic router** uses to skip the LLM. The more accurate your verbs, the cheaper your harness runs.

## Step 3 — Define your capabilities

A capability is *the thing actions are applied to*. For us:

```json
{
  "capabilities": {
    "Ticket": {
      "actions": ["lookup", "set_status", "reply", "escalate"],
      "aliases": ["case", "issue"],
      "parameters": {
        "id":     { "pattern": "^T-[0-9]+$" },
        "status": { "values": ["open", "pending", "resolved", "closed"] },
        "team":   { "values": ["tier1", "tier2", "billing", "engineering"] },
        "body":   { "type": "string", "max_length": 4000 }
      },
      "state": { "last_seen_id": null }
    }
  }
}
```

Note three things:

- **`pattern`** prevents the agent from inventing ticket IDs.
- **`values`** enumerates allowed statuses — no free-text drift.
- **`max_length`** keeps reply bodies bounded.

## Step 4 — Add a scenario

A scenario is a deterministic multi-step macro. We will model "first response":

```json
{
  "scenarios": {
    "first_response": {
      "description": "Reply to a new ticket and set it to pending.",
      "steps": [
        { "target": "Ticket", "action": "reply",      "parameters": { "body": "Hi, thanks for reaching out — we're looking into this." } },
        { "target": "Ticket", "action": "set_status", "parameters": { "status": "pending" } }
      ]
    }
  }
}
```

The agent can now invoke `scenario("first_response")` and Literal will execute both steps atomically.

## Step 5 — Write the policy

Save this to `literal.policy.json`:

```json
{
  "fuzzy_cutoff": 0.7,
  "inspect_verbs": ["status", "show", "what is"],
  "scenario_verbs": ["run", "execute", "trigger"],
  "synonyms": {
    "resolved": ["done", "fixed"],
    "open":     ["new", "fresh"]
  },
  "confirmations": [
    { "target": "Ticket", "action": "escalate", "reason": "Escalations notify other teams; require explicit confirmation." }
  ],
  "deny": [
    { "target": "Ticket", "action": "reply",  "reason": "Replies require human review until QA is enabled." }
  ]
}
```

What you just declared:

- "escalate" needs an explicit confirmation flag from the caller.
- "reply" is **blocked outright** for now (a typical safety posture early in rollout).

## Step 6 — Doctor

```bash
literal doctor
```

Doctor walks every cross-reference: action verbs, capability names, scenario steps, deny entries, confirmation entries. Any typo surfaces here — not at runtime.

## Step 7 — Simulate from Python

```python
from literal import harness

h = harness("literal.catalog.json", "literal.policy.json")

print(h.simulate("look up T-42"))
print(h.simulate("mark T-42 as resolved"))
print(h.simulate("reply to T-42"))         # should be denied by policy
print(h.simulate("escalate T-42 to tier2")) # should require confirmation
print(h.simulate("run first response"))    # scenario
```

Inspect what came back:

- `route` = `fast_path` when the router resolved without the LLM.
- `outcome` = `denied` / `requires_confirmation` / `completed` / `invalid`.
- `trace.matches` = every candidate the router considered, with scores.

## Step 8 — Open Literal Studio

```bash
literal dev
```

Visit `http://127.0.0.1:8787`. Use **Simulator** to retry the prompts above and watch the trace timeline populate. Switch to **Traces** and pin a denied call. This is what an auditor would see.

## Step 9 — Connect a real agent over MCP

Drop this into Cursor's `~/.cursor/mcp.json`, Claude Desktop's `claude_desktop_config.json`, or any MCP client:

```json
{
  "mcpServers": {
    "support-desk": {
      "command": "python",
      "args": [
        "-m", "literal.mcp_server",
        "--catalog", "literal.catalog.json",
        "--policy", "literal.policy.json"
      ]
    }
  }
}
```

The agent now sees `invoke`, `inspect`, `scenario` and the `literal://catalog` resource. Ask it: *"please mark ticket T-42 as resolved"*. Watch the trace appear in Studio.

## Step 10 — Loosen the policy after validation

Once you trust the agent for replies, remove the `deny` entry for `reply` and replace it with a `confirmations` entry. Re-run `doctor`. No code change is required.

This is the everyday Literal workflow: **policies move; code does not**.

---

## What you should have internalized

1. Catalog = vocabulary the agent is allowed to use.
2. Policy = guardrails the agent cannot circumvent.
3. Router = deterministic shortcut for clear inputs.
4. Validator = enforcer for everything the LLM produces.
5. Trace = the source of truth when something goes wrong.

## Next steps

- Read [Use Cases](use-cases.md) for templates you can adapt.
- Read [Policy Reference](policy-reference.md) to learn every guardrail option.
- Read [MCP Integration](mcp-integration.md) for production wiring.
