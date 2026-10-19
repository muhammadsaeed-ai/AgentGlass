# Security Policy

## Reporting a vulnerability

Please do not publish secrets, exploitable payloads, or private trace files in public issues. Use GitHub's private vulnerability reporting feature for this repository when it is enabled; otherwise contact the repository maintainer through a private channel before sharing technical details.

## Data-handling boundaries

- AgentGlass records observable events passed to it by the application. It does not inspect private model reasoning.
- The default redactor masks values under common credential/PII keys and masks several recognizable inline token/email patterns.
- Redaction is defense in depth, not a complete data-loss-prevention system. New token formats and domain-specific identifiers may not be recognized.
- Trace files can still contain confidential business context. Protect local storage, inspect exports before sharing, and never commit real user traces.
- The current package makes no network calls itself. Your instrumented application and its dependencies may make network calls independently.
- There is no hosted ingestion endpoint, authentication layer, or multi-tenant server in this MVP.

Please include a minimized synthetic reproduction in reports where possible.
