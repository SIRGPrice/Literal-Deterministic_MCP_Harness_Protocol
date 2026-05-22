"""Compact prompt builder for model-assisted routes."""

from __future__ import annotations

from .registry import CapabilityRegistry


class PromptCacheBuilder:
    """Builds a stable, compact system prompt from a registry."""

    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry

    def build(self) -> str:
        targets = ", ".join(self.registry.target_names(include_groups=True))
        actions = ", ".join(self.registry.action_names())
        scenarios = ", ".join(self.registry.scenario_names()) or "none"
        parameter_lines: list[str] = []
        for target in self.registry.target_names(include_groups=False):
            parameters = self.registry.parameter_names_for_target(target)
            if parameters:
                parameter_lines.append(f"- {target}: {', '.join(parameters)}")
        parameter_block = "\n".join(parameter_lines) if parameter_lines else "- none"

        return f"""You are an agentic tool planner connected to Literal — Deterministic MCP Harness Protocol.
Return concise tool decisions and prefer exact catalog names.

TOOLS:
- invoke(target, action, parameters): execute one catalog action.
- inspect(target): read current target state.
- scenario(name): run a named scenario.

CATALOG:
- Targets: {targets}
- Actions: {actions}
- Scenarios: {scenarios}

TARGET PARAMETERS:
{parameter_block}

RULES:
1. Use exact target, action, parameter, and scenario names when possible.
2. Keep parameters as a flat object.
3. Do not invent targets, actions, or parameter values.
4. If a request is unclear, ask a short clarification.
5. The harness validates every generated call before execution.
""".strip()
