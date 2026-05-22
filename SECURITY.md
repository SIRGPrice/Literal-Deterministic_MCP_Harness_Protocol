# Security Policy

## Supported Versions

Security review and fixes are provided for commercially licensed versions. Public evaluation builds are provided as-is under the repository license.

## Reporting A Vulnerability

Do not open a public issue for vulnerabilities that expose exploit details, secrets, customer configurations, or infrastructure internals. Send a private report with:

- Affected version or commit
- Reproduction steps
- Impact assessment
- Suggested remediation, if known
- Whether the issue was found in evaluation or licensed use

## Security Model

Literal — Deterministic MCP Harness Protocol is designed to reduce risk in agentic tool execution by adding:

- deterministic pre-model routing for simple commands;
- post-generation validation before any tool is invoked;
- explicit allow, deny, and confirmation policies;
- compact prompts that avoid oversized tool schemas;
- decision traces for audit and incident review;
- local-first configuration with no required telemetry.

Users remain responsible for secrets management, infrastructure hardening, endpoint authentication, model selection, and policy review before production deployment.
