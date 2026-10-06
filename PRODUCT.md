# agentignore — free and open source, Codex only

## Commitment

All project features are permanently free and MIT licensed. No paid edition, subscription, account requirement, telemetry or license gate is planned. Keep permission configuration and reports local. The project focuses exclusively on Codex; it does not maintain adapters for other clients.

## Users and purpose

Individual developers using Codex on personal projects or client repositories need an understandable way to review sensitive-file access and exclude irrelevant context. The core workflow is: choose a policy, preview, sync, review an offline report, then verify a harmless canary. Static checks must remain clearly distinguished from observed sandbox enforcement.

## Implemented in 0.4

- Secrets and balanced presets with validated versioned project settings.
- Codex profile compilation, additive merging, permission-only previews and private file modes.
- First-write backups and explicit restoration with a preserved pre-restoration snapshot.
- Read-only diagnostics and a macOS Codex canary without model/API calls.
- Offline searchable HTML, JSON, Markdown and SARIF reports.
- Configurable risk thresholds and explicit expiring low/medium acknowledgements.
- Actionable migration errors for older multi-client project preferences.

## Open-source priorities

1. Exercise Codex behavior on each supported platform before advertising runtime verification there.
2. Maintain compatibility fixtures for permission profiles and test conflicts with legacy settings.
3. Improve secret-detection accuracy and report clarity without hiding incomplete coverage.
4. Make common workflows easy to reproduce from source and packaged releases.
5. Add interface conveniences only when they simplify the local workflow; keep every feature free.

The HTML report is an offline snapshot, not a live policy editor. Cross-platform canaries and a desktop application are not shipped. No paid launch or billing work remains in scope.

## Feedback and contribution

Use GitHub issues or pull requests. Reproduction cases should use fake credentials and minimal example settings, not private repository contents. Measure whether a newcomer can understand the report and complete preview/sync/verification, and whether unnecessary exclusions interrupt their work. A small amount of consented user feedback is more useful than unsupported usage or savings claims.
