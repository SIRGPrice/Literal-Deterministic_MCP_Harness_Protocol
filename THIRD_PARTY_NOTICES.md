# Third-Party Notices

This repository is designed to keep the Python core dependency-light. Optional integrations and Literal Studio use third-party packages governed by their own licenses.

## Python Optional Dependencies

| Package | Purpose | License |
| --- | --- | --- |
| `mcp` | Optional Model Context Protocol server adapter | See package metadata |
| `pytest` | Development tests | MIT |
| `pytest-asyncio` | Async test support | Apache-2.0 |

## Literal Studio Dependencies

The React Studio app declares its dependencies in `apps/studio/package.json`. Before commercial redistribution, run dependency license collection for the exact lockfile used in the release and update this notice.

Suggested commands after install:

```bash
pnpm --dir apps/studio licenses list
pip install pip-licenses
pip-licenses --format=markdown
```

This file is informational and does not replace the license terms of each third-party component.
