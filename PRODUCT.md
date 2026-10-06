# agentignore Personal — commercial pilot plan

Status: local product MVP, not a launched paid service. The CLI remains MIT licensed. Pricing below is a hypothesis to validate, not an active offer or a statement about market demand.

## Who it is for

An individual developer who uses Codex, Claude Code, or both on side projects and client work. They want to know what their agent can potentially read, reduce distracting context, and avoid maintaining incompatible permission files by hand.

The first useful promise: **review and configure one project's agent access in under five minutes**. This is an onboarding target to measure; it is not a tested guarantee. The software must never claim to eliminate all credential leaks or to save a fixed amount of tokens.

## What is shipped in 0.3

- Two deliberate presets: secret filename exclusions, or secrets plus common generated/dependency directories.
- Versioned `.agentignore.toml` personal project preferences, with strict validation and an optional single-client target.
- Installation diagnostics, permission-only previews, merged settings and first-write backups.
- An offline HTML report with searchable findings, severity filters, clear next steps and a visible verification boundary.
- Stable finding IDs, schema-versioned JSON, SARIF output and configurable failure thresholds.
- Explicit low/medium-risk acknowledgements with reasons and expiry. High/critical findings and configuration errors cannot be hidden by a baseline.
- A macOS Codex fake-secret canary command that tests the explicit local profile without making a model request.

No source upload, account, telemetry, cloud backend, payment processor or artificial license gate is included. HTML reports contain filenames and masked findings; users should review reports before sharing them.

## Commercial packaging

Keep the open CLI useful. Sell convenience, maintenance and support around it. The current code is free; a paid version must offer additional delivered value.

| Package | Proposed contents | State |
| --- | --- | --- |
| Open CLI | All current features, local policy compilation, reports and documented limits | Implemented |
| Personal desktop | Project library, visual policy editor, permission preview, local history, signed installers and one-click updates | Planned, not implemented |
| Optional support | Guided configuration review using fake canaries; explain boundaries and conflicts | Requires an actual service process before sale |

For a first pilot, test a **US$19 one-time desktop license** including the delivered release and one year of updates, only after installers and update/support commitments exist. Do not promise lifetime updates. A subscription should wait until recurring maintenance, compatibility monitoring or another recurring benefit is proven. No checkout should accept payment for features listed as planned.

## Pilot acceptance criteria

Recruit five individual developers only with their consent. Do not send unsolicited messages automatically. Give them the install package, the three-minute quickstart and a synthetic demo report.

Measure, with consent and without collecting source code or secrets:

1. Time from installation to the first understandable report.
2. Whether the user can distinguish static coverage from runtime verification.
3. Whether at least one useful configuration change is previewed and applied.
4. Whether findings produce unnecessary blocking or cause needed files to become inaccessible.
5. Whether the user returns within a week and would pay for the planned convenience.

Proposed decision gate: four of five complete onboarding without assistance; three return for another project or a second check; at least two explicitly commit to paying for a concrete desktop build. These are founder-defined thresholds, not validated conversion forecasts. A small pilot cannot establish general market demand.

## What must exist before paid launch

- Actual Claude client enforcement tests and Codex tests across supported platforms; otherwise explicitly narrow the supported paid platform.
- A consistent visual interface for policy edits, preview, backup recovery and verification, with error states tested.
- Versioned compatibility fixtures, regression CI and release checksums. GitHub workflow installation currently needs the account's workflow permission; a CI template is supplied separately.
- Signed/notarized macOS installer if selling a macOS desktop application, and a defined update/support period.
- Real payment integration, license delivery, refund/support process and reviewed sales/privacy terms. None is implemented here.
- A demonstrated reason to buy beyond the free CLI. If users only want initial setup, consider a paid setup service instead of a subscription.

## Scope of the next build

Implement the desktop project's local storage, policy editor and safe preview first. The local HTML dashboard is a validated report artifact, not a finished desktop application. Avoid collecting repository contents in a backend merely to create a subscription business.
