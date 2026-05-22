# Getting Started

This page takes you from zero to a running Literal harness with a working Studio in about five minutes.

## Prerequisites

- Python 3.11 or newer
- Node.js 20+ (only if you plan to rebuild Literal Studio yourself)
- A shell (PowerShell, bash, zsh — all fine)

## 1. Install Literal

From a clone of the repo:

```bash
python -m pip install -e .
```

Or, once you have a wheel, simply:

```bash
python -m pip install literal
```

Add the MCP adapter if you want stdio integration with agent runtimes:

```bash
python -m pip install 'literal[mcp]'
```

Verify the CLI is on your PATH:

```bash
literal --help
```

If `literal` is not on your PATH, you can always invoke the module directly:

```bash
python -m literal.cli --help
```

## 2. Initialize a project

```bash
literal init
```

This creates:

- `literal.catalog.json` — declares your actions and capabilities (the "tool surface")
- `literal.policy.json` — declares matching rules, confirmations, deny gates
- `.literal/` — runtime state and trace storage

You now have a fully working sample harness modelled around a *Smart Office* domain.

## 3. Validate your configuration

```bash
literal doctor
```

`doctor` parses your catalog and policy, checks all cross-references, and prints a green report if everything is consistent. Treat any warning as a bug — fix it before continuing.

## 4. Start Literal Studio

```bash
literal dev
```

This launches the local HTTP API and serves the built Literal Studio frontend at:

```
http://127.0.0.1:8787
```

You can now:

- browse capabilities and policies,
- run scenarios,
- simulate prompts and see the routing decision,
- watch decision traces appear in real time.

## 5. Your first simulation (Python)

In another shell:

```python
from literal import harness

h = harness("literal.catalog.json", "literal.policy.json")

print(h.simulate("turn on lobby lights"))
print(h.simulate("status lobby lights"))
print(h.simulate("run opening mode"))
```

Each call returns a dict with `ok`, `route`, `target`, `action`, `parameters`, and a full `trace`.

## 6. Your first simulation (HTTP)

```bash
curl -X POST http://127.0.0.1:8787/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"text":"turn on lobby lights"}'
```

## 7. Your first MCP call

Add Literal to any MCP-aware client (Claude Desktop, Cursor, Continue, OpenAI Agents, LangChain) using:

```json
{
  "mcpServers": {
    "literal": {
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

You will see three tools (`invoke`, `inspect`, `scenario`) and two resources (`literal://catalog`, `literal://traces`).

## What's next

- Read [Core Concepts](concepts.md) to understand *why* this works.
- Follow the [Step-by-Step Tutorial](tutorial.md) to model your own domain.
- Browse [Use Cases](use-cases.md) for inspiration.
