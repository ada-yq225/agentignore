# Contributing

agentignore is permanently free, MIT licensed and Codex only. Contributions should improve local permission configuration, audit accuracy, reports or recoverability without introducing accounts, telemetry, paid gates or other-client adapters.

## Development

Use Python 3.9 or later and a virtual environment:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
python -m pytest -q
```

On macOS with Codex CLI installed, `AGENTIGNORE_RUN_CODEX_CANARY=1 python -m pytest -q` runs an opt-in fake-secret sandbox test. It supplies trust only for that invocation and makes no model call. Ordinary tests skip the runtime test. Other platforms are not runtime-verified yet.

## Changes

- Reproduce bugs with synthetic filenames and fake credentials. Do not post real secrets or private configurations.
- Preserve unrelated TOML settings, private file modes and the distinction between static coverage and runtime enforcement.
- For permission or recovery changes, add regression checks covering failures and absence of partial writes as appropriate.
- Explain the user-visible behavior and relevant validation in a pull request. Do not describe static configuration as guaranteed protection.
- Update the README and changelog when commands or supported configuration change.

Build release artifacts using `python -m pip install build` and `python -m build`. Check an installed wheel in a fresh virtual environment before releasing. Runtime support must be backed by observed client tests; do not infer it from matching generated text.
