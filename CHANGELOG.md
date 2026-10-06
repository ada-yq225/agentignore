# Changelog

## 0.3.0 — Personal product MVP

- Add versioned personal project preferences, secrets/balanced presets, client selection and read-only installation diagnostics.
- Add permission-only previews without exposing unrelated configuration values.
- Add actionable findings, stable IDs, JSON schema version, SARIF 2.1.0 and an offline searchable HTML report.
- Separate default high-risk blocking from medium artifact recommendations. `is_clean` remains an all-findings signal; `gate_failed` determines threshold failure.
- Add explicit, time-limited low/medium acknowledgements that cannot hide high/critical findings or configuration errors.
- Add a macOS Codex explicit-profile fake-secret verification command.
- Stop classifying public SSH keys and public certificate extensions as sensitive by filename alone; fix Anthropic signature classification.
- Document a personal-user commercial pilot while keeping the CLI MIT licensed. Desktop, accounts, billing and paid entitlements remain unimplemented.

## 0.2.0 — Actual client adapters

- Replace unsupported vendor ignore files with documented Codex and Claude Code settings.
- Treat `.agentignore` as input, add backups and preflight checks, and correct protection/cost claims.
- Narrow all audit claims to static project-local assessment.
