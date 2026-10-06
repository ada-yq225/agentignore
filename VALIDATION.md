# Validation for the Codex / Claude adapters

Validated on 2026-10-06, macOS arm64, Python 3.13.5, Codex CLI 0.159.2.

- `AGENTIGNORE_RUN_CODEX_CANARY=1 python -m pytest -q`: **118 passed**.
- The opt-in runtime test loads the generated project `.codex/config.toml`, explicitly selects the `agentignore` permission profile, and supplies trust for the temporary directory as an invocation-local override. `/bin/cat public.txt` succeeds; `/bin/cat .env.agentignore-canary` fails with `Operation not permitted`. No model/API request, real credential, user settings mutation, or persistent trust change is involved.
- Source distribution and wheel build successfully. The wheel installs into a fresh virtual environment; CLI `sync` and JSON `check` smoke tests pass, with `runtime_verified: false`.
- `git diff --check` passes.
- A GitHub Actions template for Python 3.9 and 3.13 on Linux is supplied separately. The current GitHub OAuth authorization lacks workflow scope, so no workflow is committed. The macOS runtime test is opt-in and skipped in ordinary CI.

Claude Code is not installed in the validation environment. Its JSON output, merge behavior and modeled matching are tested, but **Claude client enforcement has not been exercised**. Other Codex platforms, inherited user/managed configuration, cloud tasks and MCP access are not validated by this macOS canary.

A passing canary proves the observed local sandbox behavior for that invocation. It does not establish a universal safety boundary or prove which profile ordinary sessions will select.
