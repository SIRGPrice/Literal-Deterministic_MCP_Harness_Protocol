# MCP Integration

Literal ships an [MCP](https://modelcontextprotocol.io) server (`literal.mcp_server`) so any MCP-aware client can call your harness over stdio.

## Install the optional dependency

```bash
python -m pip install 'literal[mcp]'
```

This pulls the official `mcp` Python SDK.

## Run the server manually

```bash
python -m literal.mcp_server \
    --catalog literal.catalog.json \
    --policy  literal.policy.json
```

The server reads MCP messages from stdin and writes responses to stdout. Logs go to stderr. Add `--state` and `--traces` to override defaults.

## Exposed tools

| Tool | Signature | Purpose |
| --- | --- | --- |
| `invoke` | `invoke(target: str, action: str, parameters_json: str = "{}")` | Structured tool call. |
| `inspect` | `inspect(target: str)` | Read capability state. |
| `scenario` | `scenario(name: str)` | Execute a named scenario. |

`parameters_json` is a JSON-encoded string to keep the tool schema stable across clients with different JSON support.

## Exposed resources

| URI | Purpose |
| --- | --- |
| `literal://catalog` | Current catalog (read-only). |
| `literal://traces`  | Recent decision traces (read-only). |

Agents that load resources get a compact representation of "what they can do" plus an audit feed they can reason about.

---

## Client recipes

### Anthropic `mcp` Python SDK

```python
import asyncio, json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="python",
        args=["-m", "literal.mcp_server",
              "--catalog", "literal.catalog.json",
              "--policy",  "literal.policy.json"],
    )
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            print(await s.list_tools())
            print(await s.list_resources())
            print(await s.call_tool("invoke", {
                "target": "Lobby lights",
                "action": "turn_on",
                "parameters_json": "{}",
            }))

asyncio.run(main())
```

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "literal": {
      "command": "python",
      "args": [
        "-m", "literal.mcp_server",
        "--catalog", "C:\\path\\to\\literal.catalog.json",
        "--policy",  "C:\\path\\to\\literal.policy.json"
      ]
    }
  }
}
```

Restart Claude Desktop. The tools appear in the hammer icon.

### Cursor

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "literal": {
      "command": "python",
      "args": ["-m", "literal.mcp_server",
               "--catalog", "literal.catalog.json",
               "--policy",  "literal.policy.json"],
      "cwd": "C:\\path\\to\\project"
    }
  }
}
```

### Continue, Cline, Windsurf, Zed

All follow the same `mcpServers` schema. Use `literal export --format mcp` to generate the snippet for your project.

### LangChain

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "literal": {
        "command": "python",
        "args": ["-m", "literal.mcp_server",
                 "--catalog", "literal.catalog.json",
                 "--policy",  "literal.policy.json"],
        "transport": "stdio",
    }
})
tools = await client.get_tools()
```

### OpenAI Agents SDK

```python
from agents.mcp import MCPServerStdio

server = MCPServerStdio(params={
    "command": "python",
    "args": ["-m", "literal.mcp_server",
             "--catalog", "literal.catalog.json",
             "--policy",  "literal.policy.json"]
})
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Client shows no tools | Wrong `cwd`; catalog/policy not found | Use absolute paths or set `cwd`. |
| "ModuleNotFoundError: literal" | Wrong Python interpreter | Use the absolute path of the interpreter where you installed Literal. |
| Tools listed but `invoke` errors | Server can't write state/traces | Pass writable `--state` and `--traces` paths. |
| Calls always denied | A policy `deny` covers them | Inspect via `literal://catalog` and adjust the policy. |
| Confirmation loop | Caller never sets `confirmed: true` | Surface a confirmation UI in your client. |

## Security

The stdio server inherits the privileges of the process that launched it. Treat the catalog and policy files as the agent's blast radius — if it is not in the catalog, the agent cannot call it. See [Security](security.md).

## Related

- [HTTP API](http-api.md) — if you would rather connect over HTTP than MCP.
- [Python SDK](python-sdk.md) — to embed Literal directly in your own runtime.
