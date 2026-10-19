"""Run and span recording API for instrumenting agent workflows."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import threading
import time
import uuid
from typing import Any, Iterator

from .models import EventType, TraceEvent
from .redaction import Redactor
from .storage import EventStore, InMemoryStore


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class SpanHandle:
    """Mutable result handle yielded by a span/tool context manager."""

    def __init__(self) -> None:
        self.output: Any = None
        self.has_output = False

    def set_output(self, value: Any) -> None:
        """Attach an observed result; it is redacted before it reaches storage."""
        self.output = value
        self.has_output = True


class RunTrace:
    """A single run. Events share one run ID and are appended in sequence order."""

    def __init__(self, tracer: "AgentGlass", run_id: str) -> None:
        self._tracer = tracer
        self.run_id = run_id
        self._sequence = 0
        self._lock = threading.RLock()
        self._finished = False
        self._emit(
            EventType.RUN_STARTED,
            name="run",
            status="started",
            attributes={"service_name": tracer.service_name},
        )

    def _append_locked(
        self,
        event_type: EventType,
        *,
        name: str,
        status: str,
        attributes: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        parent_event_id: str | None = None,
    ) -> TraceEvent:
        safe_attributes = self._tracer.redactor.sanitize(attributes or {})
        event = TraceEvent(
            event_id=uuid.uuid4().hex,
            run_id=self.run_id,
            sequence=self._sequence,
            timestamp=_utc_now(),
            event_type=event_type,
            name=name,
            status=status,
            duration_ms=duration_ms,
            parent_event_id=parent_event_id,
            attributes=safe_attributes,
        )
        self._tracer.store.append(event)
        self._sequence += 1
        return event

    def _emit(
        self,
        event_type: EventType,
        *,
        name: str,
        status: str,
        attributes: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        parent_event_id: str | None = None,
    ) -> TraceEvent:
        with self._lock:
            if self._finished:
                raise RuntimeError("Cannot record events after a run has finished")
            return self._append_locked(
                event_type,
                name=name,
                status=status,
                attributes=attributes,
                duration_ms=duration_ms,
                parent_event_id=parent_event_id,
            )

    def record(
        self,
        event_type: EventType | str,
        *,
        name: str | None = None,
        status: str = "ok",
        attributes: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        parent_event_id: str | None = None,
    ) -> TraceEvent:
        """Record a model, retry, custom, or other supported observable event."""
        try:
            normalized_type = event_type if isinstance(event_type, EventType) else EventType(event_type)
        except ValueError as exc:
            raise ValueError(f"Unsupported event type: {event_type!r}") from exc
        return self._emit(
            normalized_type,
            name=name or normalized_type.value,
            status=status,
            attributes=attributes,
            duration_ms=duration_ms,
            parent_event_id=parent_event_id,
        )

    @contextmanager
    def span(
        self,
        name: str,
        *,
        kind: str = "span",
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[SpanHandle]:
        """Record a timed operation and capture failure metadata if it raises."""
        started_at = time.perf_counter()
        start_event = self._emit(
            EventType.SPAN_STARTED,
            name=name,
            status="started",
            attributes={"kind": kind, **(attributes or {})},
        )
        handle = SpanHandle()
        try:
            yield handle
        except BaseException as exc:
            elapsed = max(0.0, (time.perf_counter() - started_at) * 1000)
            self._emit(
                EventType.SPAN_FAILED,
                name=name,
                status="error",
                duration_ms=round(elapsed, 3),
                parent_event_id=start_event.event_id,
                attributes={
                    "kind": kind,
                    **(attributes or {}),
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                },
            )
            raise
        else:
            elapsed = max(0.0, (time.perf_counter() - started_at) * 1000)
            completed_attributes = {"kind": kind, **(attributes or {})}
            if handle.has_output:
                completed_attributes["output"] = handle.output
            self._emit(
                EventType.SPAN_COMPLETED,
                name=name,
                status="ok",
                duration_ms=round(elapsed, 3),
                parent_event_id=start_event.event_id,
                attributes=completed_attributes,
            )

    @contextmanager
    def tool(
        self,
        name: str,
        *,
        input: Any = None,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[SpanHandle]:
        """Instrument a tool execution. This records events; it does not call the tool."""
        started_at = time.perf_counter()
        start_attributes = {"tool_name": name, **(attributes or {})}
        if input is not None:
            start_attributes["input"] = input
        start_event = self._emit(
            EventType.TOOL_STARTED,
            name=name,
            status="started",
            attributes=start_attributes,
        )
        handle = SpanHandle()
        try:
            yield handle
        except BaseException as exc:
            elapsed = max(0.0, (time.perf_counter() - started_at) * 1000)
            self._emit(
                EventType.TOOL_ERROR,
                name=name,
                status="error",
                duration_ms=round(elapsed, 3),
                parent_event_id=start_event.event_id,
                attributes={
                    "tool_name": name,
                    **(attributes or {}),
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                },
            )
            raise
        else:
            elapsed = max(0.0, (time.perf_counter() - started_at) * 1000)
            end_attributes: dict[str, Any] = {"tool_name": name, **(attributes or {})}
            if handle.has_output:
                end_attributes["output"] = handle.output
            self._emit(
                EventType.TOOL_COMPLETED,
                name=name,
                status="ok",
                duration_ms=round(elapsed, 3),
                parent_event_id=start_event.event_id,
                attributes=end_attributes,
            )

    def finish(
        self,
        *,
        status: str = "completed",
        output: Any = None,
        error: dict[str, Any] | str | None = None,
    ) -> TraceEvent | None:
        """Explicitly finish a run. Repeated finish calls are harmless."""
        normalized_status = status.lower()
        event_by_status = {
            "completed": (EventType.RUN_COMPLETED, "completed"),
            "failed": (EventType.RUN_FAILED, "failed"),
            "cancelled": (EventType.RUN_CANCELLED, "cancelled"),
        }
        if normalized_status not in event_by_status:
            raise ValueError("status must be 'completed', 'failed', or 'cancelled'")
        with self._lock:
            if self._finished:
                return None
            event_type, event_status = event_by_status[normalized_status]
            attributes: dict[str, Any] = {}
            if output is not None:
                attributes["output"] = output
            if error is not None:
                attributes["error"] = error
            event = self._append_locked(
                event_type,
                name="run",
                status=event_status,
                attributes=attributes,
            )
            self._finished = True
            return event

    def __enter__(self) -> "RunTrace":
        return self

    def __exit__(self, exc_type: Any, exc: BaseException | None, traceback: Any) -> bool:
        if exc is not None:
            self.finish(
                status="failed",
                error={"type": exc_type.__name__ if exc_type else "Exception", "message": str(exc)},
            )
        else:
            self.finish(status="completed")
        return False


class AgentGlass:
    """Small instrumentation client with no network calls and no runtime dependencies."""

    def __init__(
        self,
        *,
        store: EventStore | None = None,
        service_name: str = "agentglass",
        redactor: Redactor | None = None,
    ) -> None:
        if not service_name.strip():
            raise ValueError("service_name must be non-empty")
        self.store: EventStore = store if store is not None else InMemoryStore()
        self.service_name = service_name
        self.redactor = redactor if redactor is not None else Redactor()

    def start_run(
        self,
        *,
        run_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> RunTrace:
        """Create a run and immediately persist its run.started event."""
        resolved_id = run_id or uuid.uuid4().hex
        if not resolved_id.strip():
            raise ValueError("run_id must be non-empty")
        trace = RunTrace(self, resolved_id)
        if attributes:
            trace.record(
                EventType.CUSTOM,
                name="run.metadata",
                status="ok",
                attributes=attributes,
            )
        return trace

    def close(self) -> None:
        close = getattr(self.store, "close", None)
        if callable(close):
            close()
