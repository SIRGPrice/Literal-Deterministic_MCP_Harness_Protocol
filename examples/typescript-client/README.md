# TypeScript Integration Snippet

Use this pattern when your application talks to a running Literal harness over HTTP.

```ts
type SimulateResponse = {
  ok: boolean;
  route?: string;
  message?: string;
  trace?: unknown;
};

export async function simulateToolDecision(prompt: string): Promise<SimulateResponse> {
  const response = await fetch("http://localhost:8787/api/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: prompt }),
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}
```

For direct MCP usage, configure your agent runtime to launch:

```json
{
  "command": "python",
  "args": ["-m", "literal.mcp_server", "--catalog", "literal.catalog.json", "--policy", "literal.policy.json"]
}
```
