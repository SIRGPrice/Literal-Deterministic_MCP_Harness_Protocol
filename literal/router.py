"""Deterministic pre-model routing for simple agentic tool decisions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .models import MatchEvidence, RouteKind
from .registry import CapabilityRegistry
from .validator import PolicyValidator

_ARTICLES = re.compile(r"^(the|a|an|to|for|in|on|at|of)\s+", re.IGNORECASE)
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class DirectRoute:
    """A tool route resolved before the model is called."""

    kind: RouteKind
    target: str = ""
    action: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    scenario: str = ""
    confidence: float = 1.0
    reason: str = ""
    matches: tuple[MatchEvidence, ...] = ()


@dataclass(frozen=True)
class AmbiguousRoute:
    """A route that should fall through to the model."""

    text: str
    reason: str


class DeterministicRouter:
    """Classifies user text into direct tool calls when the intent is clear."""

    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        self.validator = PolicyValidator(registry)

    def classify(self, text: str) -> DirectRoute | AmbiguousRoute:
        cleaned = _clean(text)
        if not cleaned:
            return AmbiguousRoute(text=text, reason="empty input")

        scenario_route = self._try_scenario(cleaned)
        if scenario_route:
            return scenario_route

        inspect_route = self._try_inspect(cleaned)
        if inspect_route:
            return inspect_route

        invoke_route = self._try_invoke(cleaned)
        if invoke_route:
            return invoke_route

        return AmbiguousRoute(text=text, reason="no deterministic pattern matched")

    def _try_scenario(self, text: str) -> DirectRoute | None:
        for verb in sorted(self.registry.policy.scenario_verbs, key=len, reverse=True):
            prefix = f"{verb.lower()} "
            if not text.lower().startswith(prefix):
                continue
            raw_scenario = text[len(prefix):].strip()
            scenario, evidence = self._resolve_scenario(raw_scenario)
            if scenario:
                return DirectRoute(
                    kind="scenario",
                    scenario=scenario,
                    confidence=evidence.score,
                    reason="scenario verb plus fuzzy scenario match",
                    matches=(evidence,),
                )
        return None

    def _try_inspect(self, text: str) -> DirectRoute | None:
        for verb in sorted(self.registry.policy.inspect_verbs, key=len, reverse=True):
            lower_text = text.lower()
            if lower_text == verb.lower():
                return None
            if not lower_text.startswith(f"{verb.lower()} "):
                continue
            raw_target = _strip_articles(text[len(verb):].strip())
            target, evidence = self.validator.resolve_target(raw_target)
            if target:
                return DirectRoute(
                    kind="inspect",
                    target=target,
                    confidence=evidence.score,
                    reason="inspect verb plus target match",
                    matches=(evidence,),
                )
        return None

    def _try_invoke(self, text: str) -> DirectRoute | None:
        lower_text = text.lower()
        for action in self.registry.action_names():
            for alias in sorted(self.registry.aliases_for_action(action), key=len, reverse=True):
                alias_lower = alias.lower()
                if lower_text == alias_lower:
                    return None
                if not lower_text.startswith(f"{alias_lower} "):
                    continue
                remaining = _strip_articles(text[len(alias):].strip())
                parameters, remaining_target = self._extract_parameters(remaining)
                target, target_evidence = self.validator.resolve_target(remaining_target)
                if not target:
                    continue
                action_result = self.validator.validate(target=target, action=action, parameters=parameters)
                if not action_result.ok or not action_result.invocation:
                    return None
                confidence = min([target_evidence.score, *[match.score for match in action_result.matches]] or [1.0])
                return DirectRoute(
                    kind="invoke",
                    target=action_result.invocation.target,
                    action=action_result.invocation.action,
                    parameters=action_result.invocation.parameters,
                    confidence=confidence,
                    reason="action verb plus target match",
                    matches=action_result.matches,
                )
        return None

    def _extract_parameters(self, text: str) -> tuple[dict[str, Any], str]:
        remaining = text
        parameters: dict[str, Any] = {}
        all_parameter_names = set()
        for target in self.registry.target_names(include_groups=True):
            all_parameter_names.update(self.registry.parameter_names_for_target(target))

        for parameter_name in sorted(all_parameter_names, key=len, reverse=True):
            values: set[str] = set()
            for target in self.registry.target_names(include_groups=True):
                definition = self.registry.parameter_for_target(target, parameter_name)
                if definition:
                    values.update(definition.values)
            for value in sorted(values, key=len, reverse=True):
                pattern = re.compile(rf"(?:with|to|as|at|=)?\s*{re.escape(value)}\s*$", re.IGNORECASE)
                if pattern.search(remaining):
                    parameters[parameter_name] = value
                    remaining = pattern.sub("", remaining).strip()
                    remaining = re.sub(r"\s+(with|to|as|at)$", "", remaining, flags=re.IGNORECASE).strip()
                    break

        explicit_pairs = re.findall(r"(\w+)\s*[:=]\s*([\w.-]+)", remaining)
        for raw_name, raw_value in explicit_pairs:
            parameters[raw_name] = raw_value
        if explicit_pairs:
            remaining = re.sub(r"\w+\s*[:=]\s*[\w.-]+", "", remaining).strip()

        return parameters, _strip_articles(remaining)

    def _resolve_scenario(self, text: str) -> tuple[str | None, MatchEvidence]:
        candidates = self.registry.scenario_names()
        aliases = {candidate: self.registry.aliases_for_scenario(candidate) for candidate in candidates}
        from .validator import _resolve

        return _resolve(text, candidates, aliases, self.registry.policy.fuzzy_cutoff, "scenario")


def _clean(text: str) -> str:
    return _WHITESPACE.sub(" ", text.strip())


def _strip_articles(text: str) -> str:
    current = text.strip()
    while True:
        stripped = _ARTICLES.sub("", current).strip()
        if stripped == current:
            return stripped
        current = stripped
