# Validation for the Codex-only 0.4 release

Validated on 2026-10-06, macOS arm64, Python 3.13.5, Codex CLI 0.159.2.

- `AGENTIGNORE_RUN_CODEX_CANARY=1 python -m pytest -q`: **153 passed**.
- The opt-in runtime test loads the generated project `.codex/config.toml`, explicitly selects the `agentignore` permission profile, and supplies trust for the temporary directory as an invocation-local override. `/bin/cat public.txt` succeeds; `/bin/cat .env.agentignore-canary` fails with `Operation not permitted`. No model/API request, real credential, user settings mutation, or persistent trust change is involved.
- Source distribution and wheel build successfully. The wheel installs into a fresh virtual environment; CLI `sync` and JSON `check` smoke tests pass, with `runtime_verified: false`.
- `git diff --check` passes.
- The tests cover Codex-only defaults, migration rejection, unrelated-client preservation, backup restoration and failure preflights as well as project settings, risk thresholds, expiring acknowledgements, secret-safe permission previews, stable finding IDs, HTML escaping, SARIF output, installation diagnostics and verification failure states.
- A synthetic deep-scan SARIF report validates against the OASIS SARIF 2.1.0 JSON schema. Its offline HTML counterpart was inspected in the browser; search and severity filters return the expected findings, and raw synthetic credentials are absent from the report.
- `agentignore verify --target codex --json` passes the public-read/secret-denial canary on this machine. It explicitly reports that ordinary sessions and all policy paths remain unverified.
- A GitHub Actions template for Python 3.9 and 3.13 on Linux is supplied separately. The current GitHub OAuth authorization lacks workflow scope, so no workflow is committed. The macOS runtime test is opt-in and skipped in ordinary CI.

Only Codex is supported in 0.4. Other Codex platforms, inherited user/managed configuration, cloud tasks and MCP access are not validated by this macOS canary.

A passing canary proves the observed local sandbox behavior for that invocation. It does not establish a universal safety boundary or prove which profile ordinary sessions will select.
