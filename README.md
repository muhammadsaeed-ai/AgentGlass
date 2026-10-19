# AgentGlass

<p align="center">
  <img src="assets/readme/progress-loop.gif" alt="Animated workflow indicator" width="420" />
</p>

<p align="center"><strong>AI agent observability, run tracing, and tool-call inspection — designed for builders.</strong></p>
<p align="center">
  <a href="#the-problem">Problem</a> · <a href="#visual-workflow">Workflow</a> · <a href="#proposed-architecture">Architecture</a> · <a href="#roadmap">Roadmap</a>
</p>
<p align="center">
  <img alt="Stage: design proposal" src="https://img.shields.io/badge/stage-design%20proposal-7867FF?style=flat-square" />
  <img alt="Privacy by design" src="https://img.shields.io/badge/approach-local--first-168AAD?style=flat-square" />
  <img alt="Open source concept" src="https://img.shields.io/badge/project-open%20source%20concept-15A88A?style=flat-square" />
</p>

> **Project status: design-stage.** This repository currently contains the concept and README visuals only. There is no released dashboard, SDK, backend, agent-framework adapter, or executable implementation yet. The diagrams below describe the proposed product, not shipped features.

AgentGlass is a proposed **AI agent observability dashboard** for developers building tool-using agents and multi-step LLM workflows. The goal is to make an agent run explainable after it succeeds, fails, calls the wrong tool, or takes unexpectedly long.

## The problem

Agent systems can produce a chain of model decisions, tool calls, outputs, retries, and errors. Plain application logs often make it difficult to follow the whole run. AgentGlass aims to bring that sequence into one inspection surface, with event context rather than only a final answer.

## What AgentGlass aims to provide

| Planned capability | Developer value |
|---|---|
| Run timeline | See the order of model steps, tool calls, results, and errors |
| Tool-call inspection | Relate a tool request to its response and surrounding run context |
| Failure analysis | Find the step that failed and preserve its diagnostic evidence |
| Latency breakdown | Identify slow steps and repeated calls when timestamps are available |
| Token and cost context | Display usage or estimated cost only when trusted adapter data is available |
| Search and export | Filter runs and export structured traces for debugging or issue reports |
| Framework adapters | Normalize events from selected agent libraries through explicit integrations |

These are design goals, not implemented or benchmarked features. The first milestone should be a small, validated event schema and one working end-to-end trace.

## Visual workflow

<p align="center"><img src="assets/readme/workflow.svg" alt="Proposed AgentGlass workflow from capturing a run through recording tool calls, building a timeline, and investigating the trace." width="100%" /></p>

## Proposed architecture

<p align="center"><img src="assets/readme/architecture.svg" alt="Proposed AgentGlass architecture: framework adapters, a normalized event model, a trace engine, and an inspection UI." width="100%" /></p>

The initial architecture favors a small, inspectable event model. Integrations should be opt-in, provider-specific values should be clearly labeled, and the system should avoid claiming to reconstruct hidden model reasoning. It should show only observable events and data that a configured integration is permitted to collect.

## Example of the intended trace shape

The following is **illustrative JSON**, not output from a working AgentGlass implementation:

```json
{
  "run_id": "run_example_001",
  "status": "failed",
  "events": [
    {"type": "run.started", "timestamp_ms": 0},
    {"type": "tool.call", "tool": "search_docs", "timestamp_ms": 84},
    {"type": "tool.error", "tool": "search_docs", "timestamp_ms": 311},
    {"type": "run.failed", "timestamp_ms": 316}
  ]
}
```

## Design principles

- **Observable data only:** record actual events and explicitly labeled derived fields; do not pretend to expose private model reasoning.
- **Provider-neutral core:** keep the base schema independent from any single framework.
- **Privacy-aware by default:** define redaction, retention, and sensitive-value policies before collecting real user data.
- **Local-first development:** prefer a local demo and inspectable export before adding hosted services.
- **Evidence over vanity metrics:** no fabricated success rates, benchmark numbers, or usage counts.

## Roadmap

- [ ] Define and validate a versioned run/event schema.
- [ ] Build a synthetic trace generator and fixture set.
- [ ] Add a read-only local timeline viewer.
- [ ] Implement one agent-framework adapter and test event completeness.
- [ ] Add filtering, trace export, and safe error details.
- [ ] Evaluate other adapters only after the core model is stable.

## Contributing

The best early contributions are design reviews, example traces, event-schema proposals, and threat-model feedback. Please label ideas as proposals until executable code and automated tests exist.

## Search and GitHub topics

Suggested topics: `ai-agent-observability`, `llm-observability`, `agent-tracing`, `ai-agents`, `tool-call-tracing`, `llm-monitoring`, `agent-debugging`, `developer-tools`, `open-source`.

These terms describe the project direction; rankings or search traffic are not guaranteed.
