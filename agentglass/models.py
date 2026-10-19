"""Versioned, JSON-serializable event model used by AgentGlass."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import math
from typing import Any, Mapping

EVENT_SCHEMA_VERSION = "1.0"


class EventType(str, Enum):
    RUN_STARTED = "run.started"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"
    RUN_CANCELLED = "run.cancelled"
    SPAN_STARTED = "span.started"
    SPAN_COMPLETED = "span.completed"
    SPAN_FAILED = "span.failed"
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TOOL_ERROR = "tool.error"
    MODEL_REQUEST = "model.request"
    MODEL_RESPONSE = "model.response"
    RETRY = "retry"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class TraceEvent:
    """One observable event with a timezone-aware ISO-8601 timestamp."""

    event_id: str
    run_id: str
    sequence: int
    timestamp: str
    event_type: EventType
    name: str
    status: str
    attributes: dict[str, Any]
    schema_version: str = EVENT_SCHEMA_VERSION
    duration_ms: float | None = None
    parent_event_id: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != EVENT_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported schema_version {self.schema_version!r}; "
                f"expected {EVENT_SCHEMA_VERSION!r}"
            )
        if not self.event_id.strip() or not self.run_id.strip():
            raise ValueError("event_id and run_id must be non-empty")
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 0:
            raise ValueError("sequence must be a non-negative integer")
        if not isinstance(self.event_type, EventType):
            raise ValueError("event_type must be an EventType")
        if not self.name.strip() or not self.status.strip():
            raise ValueError("name and status must be non-empty")
        if not isinstance(self.attributes, dict):
            raise ValueError("attributes must be a JSON object")
        try:
            parsed = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise ValueError("timestamp must be valid ISO-8601") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        if self.duration_ms is not None:
            if (
                isinstance(self.duration_ms, bool)
                or not isinstance(self.duration_ms, (int, float))
                or not math.isfinite(self.duration_ms)
                or self.duration_ms < 0
            ):
                raise ValueError("duration_ms must be a finite, non-negative number")

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical JSON-compatible representation."""
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "name": self.name,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "parent_event_id": self.parent_event_id,
            "attributes": self.attributes,
        }

    def to_json(self) -> str:
        """Serialize one event as compact JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"), allow_nan=False)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TraceEvent":
        """Validate and construct an event from a decoded JSON object."""
        if not isinstance(payload, Mapping):
            raise ValueError("event payload must be a JSON object")
        required = {
            "event_id", "run_id", "sequence", "timestamp", "event_type",
            "name", "status", "attributes",
        }
        missing = sorted(required.difference(payload.keys()))
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        try:
            event_type = EventType(payload["event_type"])
        except (ValueError, TypeError) as exc:
            raise ValueError(f"unknown event_type: {payload.get('event_type')!r}") from exc

        duration = payload.get("duration_ms")
        if duration is not None and (
            isinstance(duration, bool) or not isinstance(duration, (int, float))
        ):
            raise ValueError("duration_ms must be a number or null")

        parent = payload.get("parent_event_id")
        if parent is not None and not isinstance(parent, str):
            raise ValueError("parent_event_id must be a string or null")

        return cls(
            schema_version=str(payload.get("schema_version", EVENT_SCHEMA_VERSION)),
            event_id=str(payload["event_id"]),
            run_id=str(payload["run_id"]),
            sequence=payload["sequence"],
            timestamp=str(payload["timestamp"]),
            event_type=event_type,
            name=str(payload["name"]),
            status=str(payload["status"]),
            duration_ms=duration,
            parent_event_id=parent,
            attributes=dict(payload["attributes"]) if isinstance(payload["attributes"], Mapping) else payload["attributes"],
        )
