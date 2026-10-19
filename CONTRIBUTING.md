# Contributing to AgentGlass

Thanks for helping make agent workflows easier to inspect. The project is an early local-first MVP; precise behavior and honest status reporting matter more than feature count.

## Before opening a change

1. Read the event contract in [docs/event-schema.md](docs/event-schema.md) and privacy notes in [docs/privacy-security.md](docs/privacy-security.md).
2. Open an issue for substantial design changes so schema compatibility and scope can be discussed.
3. Keep the core dependency-free unless a strong technical case justifies a new runtime dependency.
4. Label mock data and screenshots clearly. Do not present synthetic traces as production benchmarks.

## Development setup

Requires Python 3.11 or newer.

\`\`\`bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m agentglass demo --output traces/demo.jsonl
python -m agentglass validate traces/demo.jsonl
\`\`\`

## Pull request checklist

- [ ] Tests cover the changed behavior and failure paths.
- [ ] Trace schema changes are documented and versioning implications are explicit.
- [ ] Sensitive information is redacted before persistence; tests include adversarial input.
- [ ] Documentation distinguishes implemented behavior from future work.
- [ ] CLI output and error messages remain understandable.
- [ ] No credentials, customer traces, or private data are included in fixtures.

## Event schema compatibility

Treat event records as a public interface. Additive optional fields may be compatible; changing field meaning or removing a field requires a deliberate versioning discussion. Never claim that an adapter exists until there is runnable code and automated coverage for it.
