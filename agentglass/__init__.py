"""AgentGlass: local-first observability primitives for AI agent workflows."""

from .models import EVENT_SCHEMA_VERSION, EventType, TraceEvent
from .recorder import AgentGlass, RunTrace, SpanHandle
from .redaction import Redactor
from .storage import InMemoryStore, JSONLStore, read_events

__all__ = [
    "AgentGlass", "EVENT_SCHEMA_VERSION", "EventType", "InMemoryStore",
    "JSONLStore", "Redactor", "RunTrace", "SpanHandle", "TraceEvent", "read_events",
]

__version__ = "0.1.0"
