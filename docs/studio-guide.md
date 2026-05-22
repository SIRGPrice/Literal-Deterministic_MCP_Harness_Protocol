# Studio Guide

Literal Studio is the React UI you get with `literal dev`. It is fully local, talks only to `127.0.0.1:8787`, and is designed for three audiences: engineers building catalogs, security reviewing policies, and operators auditing decisions.

Open it at `http://127.0.0.1:8787/`.

## Dashboard

![Dashboard](assets/images/dashboard.png)

Landing page. Shows:

- catalog summary (capabilities, actions, scenarios);
- recent traces and outcome breakdown;
- policy stats (denies, confirmations);
- runtime info (server version, paths in use).

Use this as a daily sanity check.

## Capabilities

![Capabilities](assets/images/capabilities.png)

Browse every capability, the actions it accepts, its aliases, parameters, and current state. Click a capability to drill into its parameter constraints and recent activity.

Engineers use this view to verify their catalog edits.

## Policies

![Policies](assets/images/policies.png)

The policy panel exposes:

- `fuzzy_cutoff`;
- inspect and scenario verbs;
- synonyms;
- the **confirmations** list;
- the **deny** list.

Each row links back to the capability/action it affects so security reviewers can see exactly which calls a given rule covers.

## Scenarios

![Scenarios](assets/images/scenarios.png)

Browse and dry-run scenarios. Each step is shown with its target, action, and parameters. Click **Run** to execute the scenario; each step writes its own trace.

## Simulator

![Simulator](assets/images/simulator.png)

The most-used panel. Type a free-text input as the agent would emit it; Studio runs `/api/simulate` and shows:

- the route (`fast_path` / `ambiguous`);
- the matched target and action;
- the resolved parameters;
- the outcome with reason;
- a link to the trace.

Use this to *prove* a policy change before shipping.

## Traces

![Traces](assets/images/traces.png)

Append-only audit log. Filter by outcome (`completed`, `denied`, `invalid`, `requires_confirmation`, `error`), by target, or by free-text input. Click any trace to see the full record: input, route, matches, parameters, state delta, policy reason.

Pin denied or anomalous traces and share their `trace_id` with reviewers.

## Integrations

![Integrations](assets/images/integrations.png)

One-click snippets for every supported client: Anthropic mcp SDK, Claude Desktop, Cursor, Continue, Cline, Windsurf, Zed, OpenAI Agents, LangChain, plus a curl example. The same content is available from `literal export`.

## Settings

Toggle dark/light theme (persisted to `localStorage` under `literal.theme`), set Studio preferences, and view the static paths the backend is using.

## Keyboard

| Shortcut | Action |
| --- | --- |
| `g d` | Go to Dashboard. |
| `g c` | Go to Capabilities. |
| `g p` | Go to Policies. |
| `g s` | Go to Simulator. |
| `g t` | Go to Traces. |
| `/` | Focus simulator input. |
| `?` | Show shortcut help. |

## Notes

- Studio is read-only against your harness state in this release: editing the catalog or policy still happens in the JSON files. A future release will add in-Studio editing.
- All Studio actions go through the same `/api/*` endpoints documented in [HTTP API](http-api.md), so anything Studio can do, your scripts can do.
