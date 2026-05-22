"""Decision trace data structures and JSONL storage."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any

from .models import MatchEvidence


@dataclass(frozen=True)
class DecisionTrace:
    """Audit record for one deterministic or model-assisted decision."""

    id: str
    created_at: float
    route: str
    input_text: str = ""
    target: str = ""
    action: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    outcome: str = ""
    latency_ms: float = 0.0
    matches: tuple[MatchEvidence, ...] = ()
    errors: tuple[str, ...] = ()
    requires_confirmation: bool = False

    @classmethod
    def create(cls, **kwargs: Any) -> "DecisionTrace":
        return cls(id=str(uuid.uuid4()), created_at=time.time(), **kwargs)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["matches"] = [asdict(match) for match in self.matches]
        return payload


class TraceStore:
    """In-memory trace buffer with optional JSONL persistence."""

    def __init__(self, path: str | Path | None = None, max_items: int = 300):
        self.path = Path(path) if path else None
        self.max_items = max_items
        self._lock = RLock()
        self._items: list[DecisionTrace] = []
        if self.path and self.path.exists():
            self._load_existing()

    def add(self, trace: DecisionTrace) -> DecisionTrace:
        with self._lock:
            self._items.append(trace)
            self._items = self._items[-self.max_items:]
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.path, "a", encoding="utf-8") as file_handle:
                    file_handle.write(json.dumps(trace.to_dict(), ensure_ascii=False) + "\n")
        return trace

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            return [trace.to_dict() for trace in self._items[-limit:]][::-1]

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
            if self.path and self.path.exists():
                self.path.unlink()

    def _load_existing(self) -> None:
        if not self.path:
            return
        with open(self.path, encoding="utf-8") as file_handle:
            lines = file_handle.readlines()[-self.max_items:]
        for line in lines:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            matches = tuple(MatchEvidence(**match) for match in payload.get("matches", []))
            payload["matches"] = matches
            self._items.append(DecisionTrace(**payload))
