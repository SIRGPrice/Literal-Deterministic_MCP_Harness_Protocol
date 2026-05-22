"""Catalog and policy loading for generic deterministic MCP harnesses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    ActionDefinition,
    CapabilityDefinition,
    GroupDefinition,
    ParameterDefinition,
    PolicyDefinition,
    RuleDefinition,
    ScenarioDefinition,
    ScenarioStep,
)


class CatalogError(ValueError):
    """Raised when a catalog or policy document is invalid."""


class CapabilityRegistry:
    """Immutable catalog of actions, targets, groups, scenarios, and policies."""

    def __init__(self, catalog: dict[str, Any], policy: dict[str, Any] | None = None):
        self.raw_catalog = dict(catalog)
        self.raw_policy = dict(policy or catalog.get("policies", {}))
        self.name = str(catalog.get("name", "Literal Catalog"))
        self.version = str(catalog.get("version", "0.1.0"))
        self.actions = self._parse_actions(catalog.get("actions", {}))
        self.capabilities = self._parse_capabilities(catalog.get("capabilities", {}))
        self.groups = self._parse_groups(catalog.get("groups", {}))
        self.scenarios = self._parse_scenarios(catalog.get("scenarios", {}))
        self.policy = self._parse_policy(self.raw_policy)
        self._validate_references()

    @classmethod
    def from_paths(
        cls,
        catalog_path: str | Path,
        policy_path: str | Path | None = None,
    ) -> "CapabilityRegistry":
        catalog = _read_json(catalog_path)
        policy = _read_json(policy_path) if policy_path else None
        return cls(catalog=catalog, policy=policy)

    def target_names(self, include_groups: bool = True) -> list[str]:
        names = list(self.capabilities)
        if include_groups:
            names.extend(self.groups)
        return names

    def action_names(self) -> list[str]:
        return list(self.actions)

    def parameter_names_for_target(self, target: str) -> list[str]:
        capability = self.capabilities.get(target)
        if capability:
            return list(capability.parameters)
        if target in self.groups:
            member_parameters: set[str] = set()
            for member_name in self.groups[target].members:
                member = self.capabilities.get(member_name)
                if member:
                    member_parameters.update(member.parameters)
            return sorted(member_parameters)
        return []

    def parameter_for_target(self, target: str, parameter: str) -> ParameterDefinition | None:
        capability = self.capabilities.get(target)
        if capability:
            return capability.parameters.get(parameter)
        if target in self.groups:
            for member_name in self.groups[target].members:
                member = self.capabilities.get(member_name)
                if member and parameter in member.parameters:
                    return member.parameters[parameter]
        return None

    def valid_actions_for_target(self, target: str) -> list[str]:
        capability = self.capabilities.get(target)
        if capability:
            return list(capability.actions)
        group = self.groups.get(target)
        if group:
            return list(group.actions)
        return []

    def aliases_for_target(self, target: str) -> list[str]:
        capability = self.capabilities.get(target)
        group = self.groups.get(target)
        aliases: list[str] = []
        if capability:
            aliases.extend(capability.aliases)
        if group:
            aliases.extend(group.aliases)
        aliases.extend(self.policy.synonyms.get(target, ()))
        return aliases

    def aliases_for_action(self, action: str) -> list[str]:
        definition = self.actions.get(action)
        aliases = list(definition.verbs if definition else ())
        aliases.extend(self.policy.synonyms.get(action, ()))
        aliases.append(action)
        return _dedupe(aliases)

    def scenario_names(self) -> list[str]:
        return list(self.scenarios)

    def aliases_for_scenario(self, scenario: str) -> list[str]:
        definition = self.scenarios.get(scenario)
        aliases = list(definition.aliases if definition else ())
        aliases.extend(self.policy.synonyms.get(scenario, ()))
        aliases.append(scenario)
        return _dedupe(aliases)

    def initial_state(self) -> dict[str, dict[str, Any]]:
        return {
            name: dict(definition.initial_state)
            for name, definition in self.capabilities.items()
        }

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "actions": self.raw_catalog.get("actions", {}),
            "capabilities": self.raw_catalog.get("capabilities", {}),
            "groups": self.raw_catalog.get("groups", {}),
            "scenarios": self.raw_catalog.get("scenarios", {}),
            "policies": self.raw_policy,
        }

    def _parse_actions(self, raw_actions: dict[str, Any]) -> dict[str, ActionDefinition]:
        parsed: dict[str, ActionDefinition] = {}
        for name, raw_action in raw_actions.items():
            if not isinstance(raw_action, dict):
                raw_action = {}
            parsed[name] = ActionDefinition(
                name=name,
                description=str(raw_action.get("description", "")),
                verbs=tuple(str(verb) for verb in raw_action.get("verbs", [])),
                confirmation_required=bool(raw_action.get("confirmation_required", False)),
            )
        return parsed

    def _parse_capabilities(self, raw_capabilities: dict[str, Any]) -> dict[str, CapabilityDefinition]:
        parsed: dict[str, CapabilityDefinition] = {}
        for name, raw_capability in raw_capabilities.items():
            if not isinstance(raw_capability, dict):
                raise CatalogError(f"Capability '{name}' must be an object")
            parameters = self._parse_parameters(raw_capability.get("parameters", {}))
            parsed[name] = CapabilityDefinition(
                name=name,
                description=str(raw_capability.get("description", "")),
                kind=str(raw_capability.get("kind", "capability")),
                actions=tuple(str(action) for action in raw_capability.get("actions", [])),
                parameters=parameters,
                aliases=tuple(str(alias) for alias in raw_capability.get("aliases", [])),
                initial_state=dict(raw_capability.get("state", {})),
            )
        return parsed

    def _parse_parameters(self, raw_parameters: dict[str, Any]) -> dict[str, ParameterDefinition]:
        parsed: dict[str, ParameterDefinition] = {}
        for name, raw_parameter in raw_parameters.items():
            if not isinstance(raw_parameter, dict):
                raw_parameter = {"values": raw_parameter}
            numeric_range = raw_parameter.get("range")
            parsed_range = None
            if numeric_range is not None:
                if not isinstance(numeric_range, list | tuple) or len(numeric_range) != 2:
                    raise CatalogError(f"Parameter '{name}' range must contain two numbers")
                parsed_range = (int(numeric_range[0]), int(numeric_range[1]))
            parsed[name] = ParameterDefinition(
                name=name,
                description=str(raw_parameter.get("description", "")),
                values=tuple(str(value) for value in raw_parameter.get("values", [])),
                numeric_range=parsed_range,
                required=bool(raw_parameter.get("required", False)),
            )
        return parsed

    def _parse_groups(self, raw_groups: dict[str, Any]) -> dict[str, GroupDefinition]:
        parsed: dict[str, GroupDefinition] = {}
        for name, raw_group in raw_groups.items():
            if not isinstance(raw_group, dict):
                raise CatalogError(f"Group '{name}' must be an object")
            parsed[name] = GroupDefinition(
                name=name,
                description=str(raw_group.get("description", "")),
                members=tuple(str(member) for member in raw_group.get("members", [])),
                actions=tuple(str(action) for action in raw_group.get("actions", [])),
                aliases=tuple(str(alias) for alias in raw_group.get("aliases", [])),
            )
        return parsed

    def _parse_scenarios(self, raw_scenarios: dict[str, Any]) -> dict[str, ScenarioDefinition]:
        parsed: dict[str, ScenarioDefinition] = {}
        for name, raw_scenario in raw_scenarios.items():
            if isinstance(raw_scenario, list):
                raw_scenario = {"steps": raw_scenario}
            if not isinstance(raw_scenario, dict):
                raise CatalogError(f"Scenario '{name}' must be an object or list")
            steps = []
            for raw_step in raw_scenario.get("steps", []):
                if not isinstance(raw_step, dict):
                    raise CatalogError(f"Scenario '{name}' contains a non-object step")
                steps.append(
                    ScenarioStep(
                        target=str(raw_step.get("target", "")),
                        action=str(raw_step.get("action", "")),
                        parameters=dict(raw_step.get("parameters", {})),
                        description=str(raw_step.get("description", "")),
                    )
                )
            parsed[name] = ScenarioDefinition(
                name=name,
                description=str(raw_scenario.get("description", "")),
                steps=tuple(steps),
                aliases=tuple(str(alias) for alias in raw_scenario.get("aliases", [])),
            )
        return parsed

    def _parse_policy(self, raw_policy: dict[str, Any]) -> PolicyDefinition:
        return PolicyDefinition(
            fuzzy_cutoff=float(raw_policy.get("fuzzy_cutoff", 0.62)),
            inspect_verbs=tuple(str(verb) for verb in raw_policy.get("inspect_verbs", ["inspect", "status", "show", "check"])),
            scenario_verbs=tuple(str(verb) for verb in raw_policy.get("scenario_verbs", ["run", "start", "activate", "execute"])),
            deny=tuple(_parse_rules(raw_policy.get("deny", []))),
            confirmations=tuple(_parse_rules(raw_policy.get("confirmations", []))),
            synonyms={
                str(name): tuple(str(alias) for alias in aliases)
                for name, aliases in raw_policy.get("synonyms", {}).items()
            },
        )

    def _validate_references(self) -> None:
        for target, capability in self.capabilities.items():
            for action in capability.actions:
                if action not in self.actions:
                    raise CatalogError(f"Capability '{target}' references unknown action '{action}'")
        for group_name, group in self.groups.items():
            for member in group.members:
                if member not in self.capabilities:
                    raise CatalogError(f"Group '{group_name}' references unknown member '{member}'")
            for action in group.actions:
                if action not in self.actions:
                    raise CatalogError(f"Group '{group_name}' references unknown action '{action}'")
        for scenario_name, scenario in self.scenarios.items():
            for step in scenario.steps:
                if step.target not in self.capabilities and step.target not in self.groups:
                    raise CatalogError(f"Scenario '{scenario_name}' references unknown target '{step.target}'")
                if step.action not in self.actions:
                    raise CatalogError(f"Scenario '{scenario_name}' references unknown action '{step.action}'")


def _read_json(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    with open(path, encoding="utf-8") as file_handle:
        return json.load(file_handle)


def _parse_rules(raw_rules: list[dict[str, Any]]) -> list[RuleDefinition]:
    rules: list[RuleDefinition] = []
    for raw_rule in raw_rules:
        rules.append(
            RuleDefinition(
                target=str(raw_rule.get("target", "*")),
                action=str(raw_rule.get("action", "*")),
                reason=str(raw_rule.get("reason", "")),
            )
        )
    return rules


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        key = value.lower()
        if key not in seen:
            output.append(value)
            seen.add(key)
    return output
