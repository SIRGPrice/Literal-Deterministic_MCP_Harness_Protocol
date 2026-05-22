# Literal Documentation

Welcome to the Literal docs. Literal is a **Deterministic MCP Harness Protocol** for governing how agents call tools.

If you just want to install and run, jump to [Getting Started](getting-started.md). Otherwise the docs follow a deliberate learning path:

## Suggested reading order

1. **[Getting Started](getting-started.md)** — install, `literal init`, `literal dev`, first simulation.
2. **[Core Concepts](concepts.md)** — catalog, policy, router, validator, traces, scenarios.
3. **[Step-by-Step Tutorial](tutorial.md)** — model a real domain end-to-end and observe every layer.
4. **[Use Cases](use-cases.md)** — concrete problems Literal solves, by industry and team.
5. **[Advanced Examples](advanced-examples.md)** — complex, runnable fixtures for hospital command, fintech risk ops, and grid orchestration.
6. **[Architecture](architecture.md)** — why determinism, prompt compaction, and post-generation validation matter.

## Reference

- **[Catalog Reference](catalog-reference.md)** — every field, every type.
- **[Policy Reference](policy-reference.md)** — fuzzy cutoff, deny, confirmations, synonyms.
- **[CLI Reference](cli-reference.md)** — `literal init/doctor/dev/add-tool/export`.
- **[Python SDK](python-sdk.md)** — `from literal import harness` and lower-level classes.
- **[HTTP API](http-api.md)** — endpoints exposed by `literal dev`.
- **[MCP Integration](mcp-integration.md)** — stdio adapter, tools, resources, client recipes.
- **[Literal Studio Guide](studio-guide.md)** — every panel, every shortcut.
- **[Security & Deployment](security.md)** — hardening, secrets, audit trails.

## Specification

- **[Literal Protocol Specification](SPEC.md)** — the formal contract that any language implementation must satisfy.

## Contributing & License

This project is source-available for evaluation only. See [LICENSE](../LICENSE) and [COMMERCIAL_LICENSE_REQUEST.md](../COMMERCIAL_LICENSE_REQUEST.md).
