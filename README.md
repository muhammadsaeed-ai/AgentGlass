<div align="center">

<img src="assets/readme/agentglass-hero.svg" alt="AgentGlass — local-first AI agent observability" width="100%" />

<p><strong>Make every run inspectable.</strong></p>
<p>Local-first tracing primitives for AI agent workflows — lifecycle events, tool-call context, failure capture, and JSONL inspection.</p>

<p>
  <a href="https://github.com/muhammadsaeed-ai/AgentGlass/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/muhammadsaeed-ai/AgentGlass/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI status" /></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/runtime%20dependencies-zero-24B89A?style=for-the-badge" alt="Zero runtime dependencies" />
  <img src="https://img.shields.io/badge/license-MIT-8274F7?style=for-the-badge" alt="MIT license" />
</p>

<p><a href="#-quick-start">Quick start</a> · <a href="#-api-at-a-glance">API</a> · <a href="docs/architecture.md">Architecture</a> · <a href="docs/event-schema.md">Event schema</a> · <a href="docs/privacy-security.md">Privacy model</a></p>

</div>

---

> **Status: early MVP / alpha.** The repository now includes a runnable Python recorder, versioned event validation, local stores, best-effort redaction, CLI trace inspection, and tests. It does **not** yet ship a web dashboard, hosted collector, or framework-specific auto-instrumentation. Architecture visuals show the implemented core and explicitly marked future modules.

## Why AgentGlass?

Agent runs can involve model requests, tool calls, intermediate operations, retries, errors, and outputs. A final answer alone does not show where time was spent or which observable step failed. AgentGlass provides a small event contract and local trace workflow that developers can embed in an application without sending trace data to a hosted service.

<table>
<tr><td width="50%" valign="top">

### 🔎 Follow the observable path

Use run, span, and tool context managers to capture ordered events, related start/end IDs, duration, status, and application-provided attributes.

</td><td width="50%" valign="top">

### 🛡️ Redact before storage

The default redactor masks common credential/PII keys and several recognizable token/email patterns, bounds payloads, and avoids serializing arbitrary object representations.

</td></tr>
<tr><td width="50%" valign="top">

### 🗂️ Keep traces local

Use the in-memory store for tests or append events to a UTF-8 JSONL file for inspection, diffing, and bug-report workflows.

</td><td width="50%" valign="top">

### 🧪 Validate the evidence

Typed event vocabulary, timezone-aware timestamps, schema versioning, readable validation errors, and CI tests help catch malformed traces instead of silently skipping them.

</td></tr>
</table>

## ✨ Visual workflow

<p align="center"><img src="assets/readme/workflow.svg" alt="AgentGlass workflow: record, normalize, protect, inspect" width="100%" /></p>

## 🧭 Architecture

<p align="center"><img src="assets/readme/architecture.svg" alt="AgentGlass architecture: application instrumentation through events, redaction, storage, and CLI inspection. Future adapters are marked as not implemented." width="100%" /></p>

For the fuller system boundaries and planned adapter approach, read [docs/architecture.md](docs/architecture.md).

## 🚀 Quick start

Requires **Python 3.11 or newer**. Runtime package dependencies: **none**.

### 1. Install from a clone

\`\`\`bash
git clone https://github.com/muhammadsaeed-ai/AgentGlass.git
cd AgentGlass
python -m pip install .
\`\`\`

For development, use \`python -m pip install -e .\`.

### 2. Generate a synthetic trace

\`\`\`bash
agentglass demo --output traces/demo.jsonl
\`\`\`

This command creates a repeatable **synthetic/offline demo**. It does not call an AI model, connect an agent framework, or send data over the network.

### 3. Inspect, validate, and summarize

\`\`\`bash
agentglass inspect traces/demo.jsonl
agentglass validate traces/demo.jsonl
agentglass summary traces/demo.jsonl
\`\`\`

Equivalent module commands work without installing the console entry point:

\`\`\`bash
python -m agentglass demo --output traces/demo.jsonl
python -m agentglass inspect traces/demo.jsonl
\`\`\`

## 🧩 API at a glance

Instrument an operation at the point where your application has a real observation. AgentGlass records the context; your application still executes the model request and tool itself.

\`\`\`python
from agentglass import AgentGlass, EventType, JSONLStore

client = AgentGlass(
    store=JSONLStore("traces/agent.jsonl"),
    service_name="knowledge-assistant",
)

with client.start_run(attributes={"workflow": "knowledge_lookup"}) as run:
    run.record(
        EventType.MODEL_REQUEST,
        name="planner",
        attributes={"provider": "example-provider", "model": "example-model"},
    )

    # Place this context manager around your real tool implementation.
    with run.tool(
        "docs.search",
        input={"query": "agent observability"},
        attributes={"system": "internal-docs"},
    ) as tool:
        result = {"matches": 3}  # Replace with the real observed result.
        tool.set_output(result)

    run.record(
        EventType.MODEL_RESPONSE,
        name="planner",
        attributes={"finish_reason": "stop"},
    )
\`\`\`

### What the recorder writes

The example produces a sequence similar to:

<pre>
run.started
custom            name="run.metadata"       # only when run attributes were supplied
model.request     name="planner"
tool.started      name="docs.search"
tool.completed    name="docs.search"        duration_ms + parent_event_id
model.response    name="planner"
run.completed
</pre>

Every persisted event has a run ID, event ID, zero-based sequence, timezone-aware timestamp, event type, status, attributes, and schema version. The tool context manager emits start and terminal events, measures elapsed duration, links the terminal event to its start event, and records/re-raises exceptions.

### Instrument a general operation

\`\`\`python
with run.span("retrieve_documents", kind="retrieval", attributes={"index": "handbook"}) as span:
    documents = retrieve_documents()  # Your application's function
    span.set_output({"document_count": len(documents)})
\`\`\`

Use \`run.record(...)\` for explicit model events, retries, or supported custom events. See [the schema contract](docs/event-schema.md) for the event vocabulary and JSON fields.

## 🧰 CLI reference

| Command | Purpose |
|---|---|
| \`agentglass demo --output PATH\` | Write synthetic trace events locally |
| \`agentglass inspect PATH\` | Print a readable event timeline |
| \`agentglass inspect PATH --run-id ID\` | Inspect one run |
| \`agentglass validate PATH\` | Validate each non-empty JSONL line |
| \`agentglass summary PATH\` | Group event types by run |
| \`agentglass --version\` | Print installed package version |
| \`agentglass --help\` | Show command help |

Malformed lines and invalid schema values are reported with a path/line reference rather than silently dropped.

## 🔐 Privacy and data handling

AgentGlass is **local-first**, but a local trace can still contain confidential data.

- Attribute values pass through recursive, best-effort redaction before persistence by the provided recorder.
- Common secret-bearing keys, recognizable bearer/API token patterns, and email addresses are masked by default.
- Text length, nesting depth, and collection size are bounded to help constrain unexpected payloads.
- Events describe data explicitly passed by your application; the library does not reveal hidden model reasoning.
- The redactor is not a complete DLP solution. Avoid collecting sensitive input at source, keep trace files private, and inspect exports before sharing them.

Read [docs/privacy-security.md](docs/privacy-security.md) and [SECURITY.md](SECURITY.md). Do not commit production traces, credentials, customer records, or private prompts.

## 🧪 Development and tests

\`\`\`bash
python -m unittest discover -s tests -v
python -m agentglass demo --output traces/demo.jsonl
python -m agentglass validate traces/demo.jsonl
\`\`\`

The test suite covers event schema round-trips and validation, nested redaction, run/tool/span lifecycle behavior, JSONL persistence, corrupt-line reporting, and CLI commands. GitHub Actions runs the tests on Python 3.11 and 3.12.

## 🗃️ Repository map

\`\`\`text
AgentGlass/
├── agentglass/
│   ├── models.py          # versioned event contract and validation
│   ├── recorder.py        # run, span, tool lifecycle instrumentation
│   ├── redaction.py       # recursive masking and payload bounds
│   ├── storage.py         # in-memory and local JSONL stores
│   ├── cli.py             # demo / inspect / validate / summary
│   └── __main__.py        # python -m agentglass
├── assets/readme/
│   ├── agentglass-hero.svg
│   ├── workflow.svg
│   ├── architecture.svg
│   └── progress-loop.gif
├── docs/
│   ├── architecture.md
│   ├── event-schema.md
│   └── privacy-security.md
├── tests/
├── .github/workflows/ci.yml
├── pyproject.toml
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
\`\`\`

## 🗺️ Roadmap

- [x] Versioned, validated event schema (v1.0)
- [x] Local run/span/tool recorder with exception capture
- [x] Recursive best-effort redaction and payload bounds
- [x] In-memory store and append-only JSONL store
- [x] Synthetic offline demo plus inspect/validate/summary CLI
- [x] Standard-library test suite and CI for Python 3.11 / 3.12
- [ ] Richer query filters, trace grouping, and structured export options
- [ ] Optional adapter for one selected agent framework with fixture-based contract tests
- [ ] Interactive local timeline UI backed by real trace files
- [ ] Measured token/cost attribution where reliable provider usage data exists
- [ ] Threat-model review before any hosted ingestion or multi-user service

Roadmap items are intentions, not shipped capabilities. Contributions should keep this distinction clear.

## 🤝 Contributing

Issues, schema design feedback, synthetic fixtures, and focused code improvements are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md), keep examples free of real customer data, and include automated tests for behavior changes.

## 🔍 Topics

Suggested repository topics: \`ai-agent-observability\`, \`llm-observability\`, \`agent-tracing\`, \`ai-agents\`, \`tool-call-tracing\`, \`llm-monitoring\`, \`agent-debugging\`, \`python\`, \`developer-tools\`, \`jsonl\`, \`open-source\`.

These terms describe the project scope; discoverability and search ranking are not guaranteed.

---

<div align="center">
<strong>AgentGlass</strong> · Inspect the events you can observe. Keep control of the data you record.
<p><sub>Open source · Local-first · Early alpha</sub></p>
</div>
