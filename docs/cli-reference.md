# CLI Reference

The `literal` command line bundles everything you need to bootstrap, validate, run, and inspect a harness.

If `literal` is not on your PATH, use `python -m literal.cli ...` instead.

## Global options

| Option | Purpose |
| --- | --- |
| `--catalog PATH` | Catalog file. Default `literal.catalog.json`. |
| `--policy PATH` | Policy file. Default `literal.policy.json`. |

These apply to every subcommand below.

---

## `literal init`

Bootstrap a new project.

```bash
literal init           # error if files exist
literal init --force   # overwrite
```

Creates:

- `literal.catalog.json`
- `literal.policy.json`
- `.literal/` runtime directory

Prints a "Next steps" message pointing to `literal doctor` and `literal dev`.

---

## `literal doctor`

Validate the catalog and policy.

```bash
literal doctor
```

Checks performed:

- JSON parses cleanly;
- every action verb is unique;
- capability `actions` reference defined actions;
- group members exist;
- scenario steps reference valid `(target, action, parameters)`;
- parameter schemas are well formed;
- confirmation and deny entries reference valid targets/actions.

Run `doctor` after every catalog or policy change. Treat warnings as errors.

---

## `literal dev`

Start the local HTTP API and serve Literal Studio.

```bash
literal dev
literal dev --host 127.0.0.1 --port 8787
literal dev --no-browser
literal dev --state .literal/state.json --traces .literal/traces.jsonl
literal dev --static-dir apps/studio/dist
```

| Option | Purpose |
| --- | --- |
| `--host` | Bind address. Default `127.0.0.1`. |
| `--port` | Port. Default `8787`. |
| `--no-browser` | Do not open a browser tab. |
| `--state PATH` | State file. Default `.literal/state.json`. |
| `--traces PATH` | Traces file. Default `.literal/traces.jsonl`. |
| `--static-dir PATH` | Override the served Studio bundle (defaults to the package's bundled assets). |

The Studio is served at `http://<host>:<port>/`. The HTTP API lives under `/api/*` — see [HTTP API](http-api.md).

---

## `literal add-tool`

Scaffold a capability.

```bash
literal add-tool "Lobby lights" --action turn_on --action turn_off --alias "entrance lights"
```

| Option | Purpose |
| --- | --- |
| `--action NAME` | Repeatable. Adds an action allowance. |
| `--alias NAME` | Repeatable. Adds an alias. |
| `--parameter "name=val1,val2"` | Repeatable. Adds an enum parameter. |

The capability is written to the current catalog. Run `doctor` afterwards.

---

## `literal export`

Print integration snippets ready to copy.

```bash
literal export
literal export --format mcp     # JSON config for MCP clients
literal export --format python  # Python SDK snippet
literal export --format http    # curl example
```

Use this to populate Claude Desktop, Cursor, Continue, OpenAI Agents, or LangChain configurations.

---

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success. |
| `1` | Missing files (run `literal init`). |
| `2` | Validation failed (`doctor`). |
| `3` | Runtime error (e.g., port in use). |

---

## Environment variables

| Variable | Purpose |
| --- | --- |
| `LITERAL_CATALOG` | Default catalog path. |
| `LITERAL_POLICY` | Default policy path. |
| `LITERAL_STATE` | Default state path. |
| `LITERAL_TRACES` | Default traces path. |

Command-line options always win over environment variables.
