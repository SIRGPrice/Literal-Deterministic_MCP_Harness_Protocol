"""Typed data models used by the deterministic harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

RouteKind = Literal["invoke", "inspect", "scenario", "ambiguous"]


@dataclass(frozen=True)
class ActionDefinition:
    """A canonical action that can be executed by a capability or group."""

    name: str
    description: str = ""
    verbs: tuple[str, ...] = ()
    confirmation_required: bool = False


@dataclass(frozen=True)
class ParameterDefinition:
    """Allowed values for a named action parameter."""

    name: str
    description: str = ""
    values: tuple[str, ...] = ()
    numeric_range: tuple[int, int] | None = None
    required: bool = False


@dataclass(frozen=True)
class CapabilityDefinition:
    """A target that the harness can invoke."""

    name: str
    description: str = ""
    kind: str = "capability"
    actions: tuple[str, ...] = ()
    parameters: dict[str, ParameterDefinition] = field(default_factory=dict)
    aliases: tuple[str, ...] = ()
    initial_state: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GroupDefinition:
    """A named group of capabilities with its own allowed actions."""

    name: str
    description: str = ""
    members: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScenarioStep:
    """One deterministic step in a scenario."""

    target: str
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass(frozen=True)
class ScenarioDefinition:
    """A repeatable sequence of tool invocations."""

    name: str
    description: str = ""
    steps: tuple[ScenarioStep, ...] = ()
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class RuleDefinition:
    """Policy rule for allow, deny, or confirmation behavior."""

    target: str = "*"
    action: str = "*"
    reason: str = ""

    def matches(self, target: str, action: str) -> bool:
        target_match = self.target == "*" or self.target.lower() == target.lower()
        action_match = self.action == "*" or self.action.lower() == action.lower()
        return target_match and action_match


@dataclass(frozen=True)
class PolicyDefinition:
    """Runtime policy settings used by router and validator."""

    fuzzy_cutoff: float = 0.62
    inspect_verbs: tuple[str, ...] = ("inspect", "status", "show", "check")
    scenario_verbs: tuple[str, ...] = ("run", "start", "activate", "execute")
    deny: tuple[RuleDefinition, ...] = ()
    confirmations: tuple[RuleDefinition, ...] = ()
    synonyms: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class MatchEvidence:
    """How free text was resolved to a canonical catalog name."""

    field: str
    requested: str
    resolved: str | None
    score: float
    method: str
    suggestions: tuple[str, ...] = ()


@dataclass(frozen=True)
class ToolInvocation:
    """Canonical tool invocation after validation."""

    target: str
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
