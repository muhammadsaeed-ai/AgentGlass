# AgentGlass Event Schema — v1.0

AgentGlass stores one JSON object per line (JSONL). The schema models observable application events, not hidden model reasoning.

## Required event fields

| Field | Type | Contract |
|---|---|---|
| \`schema_version\` | string | Currently \`1.0\`; incompatible changes require explicit versioning |
| \`event_id\` | string | Unique ID for this event |
| \`run_id\` | string | ID shared by events in one recorded run |
| \`sequence\` | integer | Zero-based insertion order within a run |
| \`timestamp\` | string | Timezone-aware ISO-8601 UTC timestamp |
| \`event_type\` | enum string | Event kind from the supported vocabulary |
| \`name\` | string | Human-readable operation or event name |
| \`status\` | string | Event status such as \`started\`, \`ok\`, \`error\`, \`completed\`, \`failed\`, or \`cancelled\` |
| \`attributes\` | object | JSON-compatible, redacted contextual values |

Optional fields are \`duration_ms\` (finite non-negative number) and \`parent_event_id\` (event ID for a related start event).

## Current event vocabulary

- Lifecycle: \`run.started\`, \`run.completed\`, \`run.failed\`, \`run.cancelled\`
- Spans: \`span.started\`, \`span.completed\`, \`span.failed\`
- Tools: \`tool.started\`, \`tool.completed\`, \`tool.error\`
- Model instrumentation hooks: \`model.request\`, \`model.response\`
- Extensibility: \`retry\`, \`custom\`

The SDK does not automatically instrument an LLM provider or run a tool. The application records these events at the point where it has reliable observations.

## Example event

\`\`\`json
{
  "schema_version": "1.0",
  "event_id": "evt_example",
  "run_id": "run_example",
  "sequence": 1,
  "timestamp": "2026-01-02T03:04:05.123Z",
  "event_type": "tool.completed",
  "name": "docs.search",
  "status": "ok",
  "duration_ms": 12.4,
  "parent_event_id": "evt_tool_start",
  "attributes": {
    "tool_name": "docs.search",
    "output": {"matches": 3}
  }
}
\`\`\`

## Ordering and validation

Sequence numbers reflect the order in which a run's events are appended to its store. Timestamps describe wall-clock time and may not be suitable as the sole ordering mechanism. Readers reject unknown event types, unsupported schema versions, invalid timestamps, invalid durations, and malformed JSONL lines rather than silently discarding them.

## Recommended extension discipline

Use \`attributes\` for integration-specific fields. Prefix or namespace fields where ambiguity is likely (for example, \`provider\`, \`model\`, \`tool_name\`). Store token counts, costs, and latency only when values are supplied by a trusted integration; label estimates explicitly.
