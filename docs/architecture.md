# Architecture

AgentGlass keeps collection, event normalization, safety checks, and persistence deliberately small so integrations can be added without coupling the core to a single framework.

\`\`\`mermaid
flowchart LR
    A["Your agent / application"] --> B["AgentGlass recording API"]
    B --> C["Run + span lifecycle"]
    C --> D["Versioned TraceEvent"]
    D --> E["Recursive redaction + bounds"]
    E --> F["Store contract"]
    F --> G["In-memory store"]
    F --> H["Local JSONL store"]
    H --> I["CLI inspect / validate / summary"]
    style B fill:#101d31,stroke:#5ee7ff,color:#f4fbff
    style D fill:#102a2b,stroke:#43e0b4,color:#f4fffb
    style E fill:#28213f,stroke:#9b8cff,color:#faf8ff
\`\`\`

## Event path

1. The application starts a run and records explicit context.
2. The recorder creates run/span/tool lifecycle events with UTC timestamps and monotonic sequence numbers.
3. Event attributes pass through recursive redaction and payload bounds before the store receives the event.
4. A store persists the canonical v1.0 JSON representation.
5. The CLI reads the same schema for inspection, validation, and run summaries.

## Core boundaries

- **Models:** versioned vocabulary and validation.
- **Recorder:** lifecycle helpers; never executes user tools or makes model calls.
- **Redactor:** best-effort masking and payload limits before persistence.
- **Storage:** replaceable store contract, in-memory implementation, append-only JSONL.
- **CLI:** local developer workflow; no telemetry or hosted connection.

## Next architecture increments

A framework adapter should live behind an optional integration module and emit the same normalized event contract. Any provider-specific token/cost data should declare its source and whether it is measured or estimated. Hosted ingestion, if ever added, requires a separate threat model, authentication, authorization, retention, and tenant-isolation design.
