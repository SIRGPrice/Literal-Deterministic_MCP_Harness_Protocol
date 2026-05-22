"""Atomic local state store for deterministic tool execution."""

from __future__ import annotations

import json
import time
from pathlib import Path
from threading import RLock
from typing import Any


class AtomicStateStore:
    """Small JSON-backed state store with atomic writes."""

    def __init__(self, path: str | Path | None = None, initial_state: dict[str, dict[str, Any]] | None = None):
        self.path = Path(path) if path else None
        self._lock = RLock()
        self._state: dict[str, dict[str, Any]] = dict(initial_state or {})
        self._revision = 0
        if self.path and self.path.exists():
            self.load()

    def load(self) -> None:
        if not self.path:
            return
        with self._lock:
            with open(self.path, encoding="utf-8") as file_handle:
                payload = json.load(file_handle)
            self._state = dict(payload.get("targets", {}))
            self._revision = int(payload.get("revision", 0))

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "revision": self._revision,
                "targets": json.loads(json.dumps(self._state)),
            }

    def inspect(self, target: str | None = None) -> dict[str, Any]:
        with self._lock:
            if target is None:
                return self.snapshot()
            return json.loads(json.dumps(self._state.get(target, {})))

    def apply(self, target: str, action: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        parameters = dict(parameters or {})
        with self._lock:
            current = dict(self._state.get(target, {}))
            current.update(parameters)
            current["last_action"] = action
            current["updated_at"] = round(time.time(), 3)
            current["status"] = _status_for_action(action)
            self._state[target] = current
            self._revision += 1
            self.persist()
            return dict(current)

    def persist(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"revision": self._revision, "targets": self._state}
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(temp_path, "w", encoding="utf-8") as file_handle:
            json.dump(payload, file_handle, indent=2, ensure_ascii=False)
        temp_path.replace(self.path)


def _status_for_action(action: str) -> str:
    normalized = action.lower()
    if normalized in {"turn_on", "enable", "open", "start"}:
        return "active"
    if normalized in {"turn_off", "disable", "close", "stop"}:
        return "inactive"
    return "updated"
