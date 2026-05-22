"""Literal harness: routing + validation + state + traces in one object."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from .registry import CapabilityRegistry
from .router import AmbiguousRoute, DeterministicRouter, DirectRoute
from .state import AtomicStateStore
from .trace import DecisionTrace, TraceStore
from .validator import PolicyValidator

Handler = Callable[[str, str, dict[str, Any]], dict[str, Any] | str]
ToolHandler = Handler  # legacy alias


class Harness:
    """Coordinates routing, validation, execution, state, and traces."""

    def __init__(
        self,
        registry: CapabilityRegistry,
        state: AtomicStateStore | None = None,
        traces: TraceStore | None = None,
        handler: Handler | None = None,
    ):
        self.registry = registry
        self.validator = PolicyValidator(registry)
        self.router = DeterministicRouter(registry)
        self.state = state or AtomicStateStore(initial_state=registry.initial_state())
        self.traces = traces or TraceStore()
        self.handler = handler

    @classmethod
    def from_paths(
        cls,
        catalog_path: str | Path,
        policy_path: str | Path | None = None,
        state_path: str | Path | None = None,
        trace_path: str | Path | None = None,
    ) -> "Harness":
        registry = CapabilityRegistry.from_paths(catalog_path, policy_path)
        state = AtomicStateStore(state_path, initial_state=registry.initial_state())
        traces = TraceStore(trace_path)
        return cls(registry=registry, state=state, traces=traces)

    def invoke(
        self,
        target: str,
        action: str,
        parameters: dict[str, Any] | None = None,
        *,
        input_text: str = "",
        route: str = "validated",
    ) -> dict[str, Any]:
        started = time.perf_counter()
        result = self.validator.validate(target=target, action=action, parameters=parameters or {})
        if not result.ok or not result.invocation:
            trace = DecisionTrace.create(
                route=route,
                input_text=input_text,
                target=target,
                action=action,
                parameters=dict(parameters or {}),
                outcome="denied" if result.denied else "validation_error",
                latency_ms=_elapsed_ms(started),
                matches=result.matches,
                errors=result.errors,
            )
            self.traces.add(trace)
            return {"ok": False, "message": result.message(), "trace": trace.to_dict(), "errors": list(result.errors)}

        invocation = result.invocation
        if invocation.requires_confirmation:
            trace = DecisionTrace.create(
                route=route,
                input_text=input_text,
                target=invocation.target,
                action=invocation.action,
                parameters=invocation.parameters,
                outcome="confirmation_required",
                latency_ms=_elapsed_ms(started),
                matches=result.matches,
                requires_confirmation=True,
            )
            self.traces.add(trace)
            return {
                "ok": False,
                "requires_confirmation": True,
                "message": f"Confirmation required for {invocation.action} -> {invocation.target}",
                "trace": trace.to_dict(),
            }

        execution_result = self._execute(invocation.target, invocation.action, invocation.parameters)
        trace = DecisionTrace.create(
            route=route,
            input_text=input_text,
            target=invocation.target,
            action=invocation.action,
            parameters=invocation.parameters,
            outcome="completed",
            latency_ms=_elapsed_ms(started),
            matches=result.matches,
        )
        self.traces.add(trace)
        return {
            "ok": True,
            "message": f"{invocation.action} completed for {invocation.target}",
            "target": invocation.target,
            "action": invocation.action,
            "parameters": invocation.parameters,
            "result": execution_result,
            "trace": trace.to_dict(),
        }

    def inspect(self, target: str | None = None) -> dict[str, Any]:
        if target is None:
            return {"ok": True, "state": self.state.snapshot()}
        resolved_target, evidence = self.validator.resolve_target(target)
        if not resolved_target:
            trace = DecisionTrace.create(
                route="inspect",
                target=target,
                outcome="validation_error",
                matches=(evidence,),
                errors=(f"Unknown target '{target}'",),
            )
            self.traces.add(trace)
            return {"ok": False, "message": f"Unknown target '{target}'", "trace": trace.to_dict()}
        state = self.state.inspect(resolved_target)
        trace = DecisionTrace.create(
            route="inspect",
            target=resolved_target,
            outcome="completed",
            matches=(evidence,),
        )
        self.traces.add(trace)
        return {"ok": True, "target": resolved_target, "state": state, "trace": trace.to_dict()}

    def scenario(self, name: str, *, input_text: str = "", route: str = "scenario") -> dict[str, Any]:
        scenario_name, evidence = self.router._resolve_scenario(name)
        if not scenario_name:
            trace = DecisionTrace.create(
                route=route,
                input_text=input_text,
                outcome="validation_error",
                matches=(evidence,),
                errors=(f"Unknown scenario '{name}'",),
            )
            self.traces.add(trace)
            return {"ok": False, "message": f"Unknown scenario '{name}'", "trace": trace.to_dict()}

        scenario = self.registry.scenarios[scenario_name]
        step_results = []
        for step in scenario.steps:
            step_results.append(
                self.invoke(
                    target=step.target,
                    action=step.action,
                    parameters=step.parameters,
                    input_text=input_text,
                    route=f"{route}:step",
                )
            )
        ok = all(result.get("ok") for result in step_results)
        trace = DecisionTrace.create(
            route=route,
            input_text=input_text,
            target=scenario_name,
            action="scenario",
            outcome="completed" if ok else "partial_failure",
            matches=(evidence,),
        )
        self.traces.add(trace)
        return {"ok": ok, "scenario": scenario_name, "steps": step_results, "trace": trace.to_dict()}

    def simulate(self, text: str) -> dict[str, Any]:
        route = self.router.classify(text)
        if isinstance(route, AmbiguousRoute):
            trace = DecisionTrace.create(
                route="ambiguous",
                input_text=text,
                outcome="model_required",
                errors=(route.reason,),
            )
            self.traces.add(trace)
            return {"ok": False, "route": "ambiguous", "message": route.reason, "trace": trace.to_dict()}
        return self._execute_route(route, text)

    def _execute_route(self, route: DirectRoute, text: str) -> dict[str, Any]:
        if route.kind == "inspect":
            result = self.inspect(route.target)
            result["route"] = "inspect"
            return result
        if route.kind == "scenario":
            result = self.scenario(route.scenario, input_text=text, route="fast_path")
            result["route"] = "scenario"
            return result
        result = self.invoke(
            target=route.target,
            action=route.action,
            parameters=route.parameters,
            input_text=text,
            route="fast_path",
        )
        result["route"] = "invoke"
        return result

    def _execute(self, target: str, action: str, parameters: dict[str, Any]) -> dict[str, Any] | str:
        if self.handler:
            return self.handler(target, action, parameters)
        return self.state.apply(target, action, parameters)

    def catalog(self) -> dict[str, Any]:
        return self.registry.as_public_dict()

    def trace_list(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.traces.list(limit=limit)


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 3)


def harness(
    catalog: str | Path = "literal.catalog.json",
    policy: str | Path | None = "literal.policy.json",
    *,
    state: str | Path | None = None,
    traces: str | Path | None = None,
    handler: Handler | None = None,
) -> Harness:
    """Build a :class:`Harness` from catalog/policy paths.

    Shortest usage::

        from literal import harness
        h = harness("literal.catalog.json", "literal.policy.json")
        h.simulate("turn on lobby lights")
    """

    h = Harness.from_paths(
        catalog_path=catalog,
        policy_path=policy,
        state_path=state,
        trace_path=traces,
    )
    if handler is not None:
        h.handler = handler
    return h


# Legacy aliases (pre-0.2)
ToolHarness = Harness

