"""Post-generation policy validation and fuzzy resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher, get_close_matches
from typing import Any

from .models import MatchEvidence, ToolInvocation
from .registry import CapabilityRegistry


@dataclass(frozen=True)
class ValidationResult:
    """Result of resolving and validating a free-form tool request."""

    ok: bool
    invocation: ToolInvocation | None = None
    errors: tuple[str, ...] = ()
    matches: tuple[MatchEvidence, ...] = ()
    denied: bool = False

    def message(self) -> str:
        if self.ok and self.invocation:
            return f"OK: {self.invocation.action} -> {self.invocation.target}"
        return "; ".join(self.errors) if self.errors else "Validation failed"


class PolicyValidator:
    """Validates model-generated tool calls against catalog and policy."""

    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        self.cutoff = registry.policy.fuzzy_cutoff

    def validate(
        self,
        target: str,
        action: str,
        parameters: dict[str, Any] | None = None,
    ) -> ValidationResult:
        parameters = dict(parameters or {})
        matches: list[MatchEvidence] = []
        errors: list[str] = []

        resolved_target, target_match = self.resolve_target(target)
        matches.append(target_match)
        if not resolved_target:
            return ValidationResult(ok=False, errors=(self._unknown_message("target", target_match),), matches=tuple(matches))

        resolved_action, action_match = self.resolve_action(action)
        matches.append(action_match)
        if not resolved_action:
            return ValidationResult(ok=False, errors=(self._unknown_message("action", action_match),), matches=tuple(matches))

        for rule in self.registry.policy.deny:
            if rule.matches(resolved_target, resolved_action):
                reason = rule.reason or "Denied by policy"
                return ValidationResult(ok=False, errors=(reason,), matches=tuple(matches), denied=True)

        valid_actions = self.registry.valid_actions_for_target(resolved_target)
        if valid_actions and resolved_action not in valid_actions:
            return ValidationResult(
                ok=False,
                errors=(
                    f"Action '{resolved_action}' is not allowed for '{resolved_target}'. Allowed: {', '.join(valid_actions)}",
                ),
                matches=tuple(matches),
            )

        resolved_parameters: dict[str, Any] = {}
        for raw_name, raw_value in parameters.items():
            resolved_name, parameter_match = self.resolve_parameter(resolved_target, raw_name)
            matches.append(parameter_match)
            if not resolved_name:
                errors.append(self._unknown_message("parameter", parameter_match))
                continue
            parameter_definition = self.registry.parameter_for_target(resolved_target, resolved_name)
            if parameter_definition is None:
                errors.append(f"Parameter '{resolved_name}' is not valid for '{resolved_target}'")
                continue
            resolved_value, value_match, value_error = self.resolve_value(parameter_definition, raw_value)
            matches.append(value_match)
            if value_error:
                errors.append(value_error)
                continue
            resolved_parameters[resolved_name] = resolved_value

        for parameter_name in self.registry.parameter_names_for_target(resolved_target):
            parameter_definition = self.registry.parameter_for_target(resolved_target, parameter_name)
            if parameter_definition and parameter_definition.required and parameter_name not in resolved_parameters:
                errors.append(f"Required parameter '{parameter_name}' is missing for '{resolved_target}'")

        if errors:
            return ValidationResult(ok=False, errors=tuple(errors), matches=tuple(matches))

        requires_confirmation = self.registry.actions[resolved_action].confirmation_required
        for rule in self.registry.policy.confirmations:
            if rule.matches(resolved_target, resolved_action):
                requires_confirmation = True

        invocation = ToolInvocation(
            target=resolved_target,
            action=resolved_action,
            parameters=resolved_parameters,
            requires_confirmation=requires_confirmation,
        )
        return ValidationResult(ok=True, invocation=invocation, matches=tuple(matches))

    def resolve_target(self, text: str) -> tuple[str | None, MatchEvidence]:
        candidates = self.registry.target_names(include_groups=True)
        aliases = {candidate: self.registry.aliases_for_target(candidate) for candidate in candidates}
        return _resolve(text, candidates, aliases, self.cutoff, "target")

    def resolve_action(self, text: str) -> tuple[str | None, MatchEvidence]:
        candidates = self.registry.action_names()
        aliases = {candidate: self.registry.aliases_for_action(candidate) for candidate in candidates}
        return _resolve(text, candidates, aliases, self.cutoff, "action")

    def resolve_parameter(self, target: str, text: str) -> tuple[str | None, MatchEvidence]:
        candidates = self.registry.parameter_names_for_target(target)
        aliases = {candidate: self.registry.policy.synonyms.get(candidate, ()) for candidate in candidates}
        return _resolve(text, candidates, aliases, self.cutoff, "parameter")

    def resolve_value(self, parameter_definition, value: Any) -> tuple[Any, MatchEvidence, str | None]:
        requested = str(value)
        if parameter_definition.values:
            resolved, evidence = _resolve(
                requested,
                list(parameter_definition.values),
                {candidate: self.registry.policy.synonyms.get(candidate, ()) for candidate in parameter_definition.values},
                self.cutoff,
                f"value:{parameter_definition.name}",
            )
            if resolved is None:
                return value, evidence, self._unknown_message("value", evidence)
            return resolved, evidence, None

        if parameter_definition.numeric_range:
            lower_bound, upper_bound = parameter_definition.numeric_range
            try:
                number = int(value)
            except (TypeError, ValueError):
                evidence = MatchEvidence(
                    field=f"value:{parameter_definition.name}",
                    requested=requested,
                    resolved=None,
                    score=0.0,
                    method="numeric",
                    suggestions=(f"{lower_bound}-{upper_bound}",),
                )
                return value, evidence, f"Value '{requested}' must be an integer from {lower_bound} to {upper_bound}"
            if number < lower_bound or number > upper_bound:
                evidence = MatchEvidence(
                    field=f"value:{parameter_definition.name}",
                    requested=requested,
                    resolved=None,
                    score=0.0,
                    method="numeric",
                    suggestions=(f"{lower_bound}-{upper_bound}",),
                )
                return value, evidence, f"Value {number} is outside range {lower_bound}-{upper_bound}"
            evidence = MatchEvidence(
                field=f"value:{parameter_definition.name}",
                requested=requested,
                resolved=str(number),
                score=1.0,
                method="numeric",
            )
            return number, evidence, None

        evidence = MatchEvidence(
            field=f"value:{parameter_definition.name}",
            requested=requested,
            resolved=requested,
            score=1.0,
            method="freeform",
        )
        return value, evidence, None

    @staticmethod
    def _unknown_message(label: str, evidence: MatchEvidence) -> str:
        if evidence.suggestions:
            return f"Unknown {label} '{evidence.requested}'. Did you mean: {', '.join(evidence.suggestions)}?"
        return f"Unknown {label} '{evidence.requested}'."


def _resolve(
    text: str,
    candidates: list[str],
    aliases: dict[str, tuple[str, ...] | list[str]],
    cutoff: float,
    field: str,
) -> tuple[str | None, MatchEvidence]:
    requested = str(text).strip()
    requested_lower = requested.lower()

    for candidate in candidates:
        if candidate.lower() == requested_lower:
            return candidate, MatchEvidence(field, requested, candidate, 1.0, "exact")

    for candidate, candidate_aliases in aliases.items():
        for alias in candidate_aliases:
            if str(alias).lower() == requested_lower:
                return candidate, MatchEvidence(field, requested, candidate, 1.0, "alias")

    searchable: dict[str, str] = {}
    for candidate in candidates:
        searchable[candidate.lower()] = candidate
        for alias in aliases.get(candidate, ()):
            searchable[str(alias).lower()] = candidate

    possible_matches = get_close_matches(requested_lower, list(searchable), n=3, cutoff=cutoff)
    if possible_matches:
        best_text = possible_matches[0]
        resolved = searchable[best_text]
        score = SequenceMatcher(None, requested_lower, best_text).ratio()
        suggestions = tuple(_dedupe(searchable[match] for match in possible_matches))
        return resolved, MatchEvidence(field, requested, resolved, score, "fuzzy", suggestions)

    loose_matches = get_close_matches(requested_lower, list(searchable), n=3, cutoff=max(0.35, cutoff - 0.22))
    suggestions = tuple(_dedupe(searchable[match] for match in loose_matches))
    return None, MatchEvidence(field, requested, None, 0.0, "miss", suggestions)


def _dedupe(values) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output
