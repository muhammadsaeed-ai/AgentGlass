# Privacy and Security Model

AgentGlass is designed to record the smallest useful account of an agent run. In its current MVP, all storage is local and the library itself does not send trace data to a service.

## Collection principles

1. **Capture observable events only.** Record tool inputs/results, timestamps, status, explicit model usage metadata, and application-defined attributes only when your integration actually observes them.
2. **Do not claim access to hidden reasoning.** A model request or response event represents data your application explicitly supplies to the recorder.
3. **Redact before persistence.** The default redactor recursively masks common sensitive keys, recognizable bearer/API token strings, and email addresses.
4. **Bound untrusted payloads.** Strings, nesting depth, and collection item counts have configurable limits.
5. **Export deliberately.** JSONL files may contain business logic, customer context, or other confidential metadata even after redaction.

## What default redaction does not guarantee

Pattern-based redaction is not a universal secret detector. It may miss custom key formats, embedded identifiers, binary payloads, secrets split across fields, or PII specific to your domain. Conversely, an application may need email addresses in a local test fixture; configure behavior consciously and test it. Avoid capturing sensitive input entirely when possible.

## Operational checklist

- Use synthetic traces in issues, examples, and CI.
- Never check API keys, production prompts, customer records, or real exported traces into source control.
- Set restrictive permissions on trace directories and delete files when no longer needed.
- Inspect any trace before sending it to a teammate or attaching it to a bug report.
- Apply your organization's retention, privacy, and access-control requirements.
- Treat trace files as sensitive operational data.

## Current limitations

This MVP has no authentication/authorization service, encryption-at-rest feature, hosted collector, multi-tenant boundary, retention scheduler, or automatic framework adapter. Those capabilities must not be implied by the local recorder or redactor.
