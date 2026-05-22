# Security & Deployment

Literal's threat model assumes the language model is **adversarial input**. The model may be jailbroken, prompt-injected, or simply wrong. Everything downstream of the model must defend itself.

This document is a hardening checklist, not a guarantee.

## Threat model

| Threat | Mitigation |
| --- | --- |
| Model emits a forbidden tool call | Validator denies; trace records the attempt. |
| Model emits a valid call with bad params | Parameter schema (`pattern`, `values`, `min`/`max`, `max_length`). |
| Prompt injection from a tool result | The catalog limits the agent's blast radius; deny-listed actions are always rejected. |
| Operator mistake (deploy with too-permissive policy) | `literal doctor`, Studio review, peer review on the policy file. |
| Compromised HTTP endpoint | Bind to `127.0.0.1`; front with auth proxy if exposed. |
| Compromised MCP stdio process | The server inherits the caller's privileges — run it as a low-privilege user. |
| Tampered trace log | Ship traces to an append-only sink (S3 + object lock, SIEM). |
| Leaked secrets in catalogs/policies | Catalogs should not contain secrets; pass them via env vars to handlers. |

## Defaults you should change before production

1. The HTTP server binds to `127.0.0.1` with **no authentication**. If you expose it beyond localhost, place an authenticated reverse proxy in front (nginx + OIDC, Cloudflare Access, Tailscale, etc.).
2. CORS is permissive for local Studio convenience. Tighten in the proxy.
3. The default policy is permissive (no deny, no confirmations). Production policies should explicitly deny destructive actions and require confirmations on impactful ones.
4. The default state and traces paths sit in `.literal/`. Move them to a managed location with backups and retention policy.

## Recommended posture

### Catalog hygiene

- Constrain every parameter that can carry a destructive value (`pattern` for IDs, `values` for enums, `max` for amounts).
- Keep aliases tight in safety-critical domains. Loose aliases produce confident fuzzy matches.
- Use groups deliberately — a fan-out group amplifies one decision into many.

### Policy hygiene

- Start strict; loosen with evidence. It is easier to allow than to recall.
- Encode confirmations on anything that: spends money, pages a human, moves something physical, sends a message externally, modifies prod.
- Encode `deny` for: production destructive actions, anything explicitly out-of-scope, kill switches during incidents.
- Review the policy on every release. Diff it like code.

### Confirmations

The Literal protocol returns `requires_confirmation` without executing. Your client must:

- surface the reason to a human;
- require an explicit action (click, signed approval, second prompt);
- only then re-invoke with the confirmation flag.

Do **not** auto-confirm in the client. That defeats the mechanism.

### Trace handling

- Ship `traces.jsonl` to a sink with append-only semantics.
- Apply PII redaction at the sink, not before — the local file is your debugging tool.
- Retain by policy. Many regulated domains require multi-year retention.
- Index by `trace_id`, `target`, `action`, `outcome` for fast retrieval during incident response.

### Process isolation

- Run one harness per tenant in multi-tenant deployments. Do not multiplex tenants through one runtime — the policy is the boundary and it is per-process today.
- Run the MCP stdio process under the least-privileged user that can perform the tools it exposes.
- Treat the catalog file as the agent's effective capability list. If the catalog is writable by an attacker, the policy is moot.

### Supply chain

- Pin the `literal` version in your `pyproject.toml` / `requirements.txt`.
- Re-run `literal doctor` in CI on every change to catalog or policy.
- Add a CI step that diffs the deny list and fails the build on unexpected removals.

## Incident response

When something goes wrong:

1. Pull recent traces filtered by `outcome != completed` from your sink.
2. Identify the input that triggered the incident.
3. Reproduce with `literal dev` → Simulator using the same input.
4. Add a `deny` or `confirmations` entry; ship the policy.
5. Backfill the affected traces with the new outcome via replay.

The harness is deterministic given a catalog + policy + input, so replay is reliable.

## Reporting vulnerabilities

If you discover a security issue, please contact the maintainer privately rather than filing a public issue. Coordinated disclosure protects users of every Literal deployment.
