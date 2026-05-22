# HTTP API

The local server is the same backend Studio uses and is the easiest way to integrate Literal with any language.

Default base URL: `http://127.0.0.1:8787`.

Server identifies itself with `Server: Literal/0.2`.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET`  | `/api/health`       | Liveness and version. |
| `GET`  | `/api/catalog`      | Current catalog. |
| `GET`  | `/api/policies`     | Current policy. |
| `POST` | `/api/simulate`     | Full pipeline on free text. |
| `POST` | `/api/invoke`       | Structured call (target/action/parameters). |
| `POST` | `/api/scenario`     | Execute a named scenario. |
| `GET`  | `/api/traces`       | List recent traces. |
| `GET`  | `/api/integration`  | Return MCP / SDK / curl snippets. |

All responses are JSON. All requests use `Content-Type: application/json`.

---

## `GET /api/health`

```json
{ "ok": true, "version": "0.2.0" }
```

## `GET /api/catalog`

Returns the parsed catalog as-loaded by the server, including resolved groups and scenarios.

## `GET /api/policies`

Returns the parsed policy.

## `POST /api/simulate`

Request:

```json
{ "text": "turn on lobby lights" }
```

Response:

```json
{
  "ok": true,
  "outcome": "completed",
  "route": "fast_path",
  "target": "Lobby lights",
  "action": "turn_on",
  "parameters": {},
  "trace_id": "trc_01HF...",
  "state": { "status": "active", "level": "low", "temperature": "warm" }
}
```

When the router cannot decide, `route` is `ambiguous` and the response includes a `matches` array.

## `POST /api/invoke`

Request:

```json
{
  "target": "Lobby lights",
  "action": "set",
  "parameters": { "level": "high" },
  "confirmed": false
}
```

Possible outcomes: `completed`, `denied`, `invalid`, `requires_confirmation`, `error`.

## `POST /api/scenario`

Request:

```json
{ "name": "opening_mode" }
```

Response:

```json
{
  "ok": true,
  "outcome": "completed",
  "scenario": "opening_mode",
  "steps": [
    { "target": "Front door", "action": "unlock", "outcome": "completed" },
    { "target": "Public areas", "action": "turn_on", "outcome": "completed" }
  ],
  "trace_id": "trc_..."
}
```

## `GET /api/traces`

Query parameters:

| Param | Default | Purpose |
| --- | --- | --- |
| `limit` | `50` | Maximum traces to return (most recent first). |
| `outcome` | — | Filter by `completed` / `denied` / etc. |
| `target` | — | Filter by capability. |

Response:

```json
{ "traces": [ { "id": "trc_...", "ts": "...", "input": "...", "outcome": "completed", ... } ] }
```

## `GET /api/integration`

Returns ready-to-copy snippets for Anthropic mcp SDK, Claude Desktop, Cursor, Continue, OpenAI Agents, LangChain, and a curl one-liner. This is what the Studio **Integrations** tab uses.

---

## Authentication

The bundled server binds to `127.0.0.1` and has **no authentication** by design. If you need to expose it to other hosts, front it with a reverse proxy that handles auth, TLS, and rate limiting (nginx, Caddy, Cloudflare Access, Tailscale). See [Security](security.md).

## CORS

By default the server emits permissive CORS headers so Studio (built or dev) can call it. Disable or tighten via reverse proxy in production.

## Errors

| Status | Meaning |
| --- | --- |
| `400` | Malformed JSON or missing required field. |
| `404` | Unknown target / scenario / trace. |
| `409` | State conflict (concurrent update). |
| `500` | Handler raised. The body includes `error.message`. |

Decision-level rejections (`denied`, `invalid`) are returned as `200` with `ok: false`, so clients can log them uniformly.
