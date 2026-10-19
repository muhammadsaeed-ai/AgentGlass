"""Storage backends for AgentGlass traces."""

from __future__ import annotations

import json
from pathlib import Path
import threading
from typing import Protocol

from .models import TraceEvent


class EventStore(Protocol):
    """Minimal contract required by the recorder."""

    def append(self, event: TraceEvent) -> None: ...
    def all(self) -> list[TraceEvent]: ...
    def for_run(self, run_id: str) -> list[TraceEvent]: ...


class InMemoryStore:
    """Thread-safe event store intended for tests and short local sessions."""

    def __init__(self) -> None:
        self._events: list[TraceEvent] = []
        self._lock = threading.RLock()

    def append(self, event: TraceEvent) -> None:
        with self._lock:
            self._events.append(event)

    def all(self) -> list[TraceEvent]:
        with self._lock:
            return list(self._events)

    def for_run(self, run_id: str) -> list[TraceEvent]:
        with self._lock:
            return [event for event in self._events if event.run_id == run_id]

    def close(self) -> None:
        """No persistent handle needs closing."""


class JSONLStore:
    """Append-only local JSON Lines store: one validated event per line."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def append(self, event: TraceEvent) -> None:
        line = event.to_json()
        with self._lock:
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(line + "\n")
                handle.flush()

    def all(self) -> list[TraceEvent]:
        if not self.path.exists():
            return []
        events: list[TraceEvent] = []
        with self._lock:
            with self.path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                        events.append(TraceEvent.from_dict(payload))
                    except (json.JSONDecodeError, TypeError, ValueError) as exc:
                        raise ValueError(
                            f"Invalid trace event at {self.path}:{line_number}: {exc}"
                        ) from exc
        return events

    def for_run(self, run_id: str) -> list[TraceEvent]:
        return [event for event in self.all() if event.run_id == run_id]

    def close(self) -> None:
        """Files are opened per operation, so no persistent handle must be closed."""


def read_events(path: str | Path) -> list[TraceEvent]:
    """Read and validate all events from a JSONL trace file."""
    return JSONLStore(path).all()
