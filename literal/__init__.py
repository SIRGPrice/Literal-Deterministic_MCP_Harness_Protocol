"""Literal — Deterministic MCP Harness Protocol.

Public Python API. The short, idiomatic entry point is:

    from literal import harness

    h = harness("literal.catalog.json", "literal.policy.json")
    print(h.simulate("turn on lobby lights"))

Class aliases keep the longer names (``ToolHarness``, ``CapabilityRegistry`` …)
available for code that wants the explicit object types.
"""

from __future__ import annotations

from .harness import Harness, harness
from .registry import CapabilityRegistry as Registry
from .router import AmbiguousRoute, DeterministicRouter as Router, DirectRoute
from .state import AtomicStateStore as StateStore
from .trace import DecisionTrace as Trace, TraceStore
from .validator import PolicyValidator as Validator, ValidationResult

# Legacy aliases (kept so older snippets keep working).
ToolHarness = Harness
CapabilityRegistry = Registry
DeterministicRouter = Router
AtomicStateStore = StateStore
DecisionTrace = Trace
PolicyValidator = Validator

__all__ = [
    "harness",
    "Harness",
    "Registry",
    "Router",
    "StateStore",
    "Trace",
    "TraceStore",
    "Validator",
    "ValidationResult",
    "AmbiguousRoute",
    "DirectRoute",
    # legacy
    "ToolHarness",
    "CapabilityRegistry",
    "DeterministicRouter",
    "AtomicStateStore",
    "DecisionTrace",
    "PolicyValidator",
]

__version__ = "0.2.0"
