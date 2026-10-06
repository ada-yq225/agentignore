# agentignore

**Project-local deny policy compiler and static auditor for Codex and Claude Code.**

Maintain one `.agentignore` input and compile it into each client's documented configuration:

| Target | Output | What is configured |
| --- | --- | --- |
| `codex` | `.codex/config.toml` | Named `agentignore` permission profile, based on `:workspace`, with workspace-scoped filesystem deny rules |
| `claude` | `.claude/settings.json` | `permissions.deny` entries for built-in `Read` and `Edit` tools |

This is a configuration tool, **not a universal security boundary**. A successful static check does not establish that a running agent cannot access your files.

## Quick start

Install from this repository (the changes in 0.2 are not yet published to PyPI):

```sh
python -m pip install .
agentignore sync --dry-run
agentignore sync
agentignore check --json
agentignore diff --target codex
```

Both clients are selected by default. Use `--targets codex` or `--targets claude` for a single client. Unknown or removed target names fail explicitly.

Before using the settings, review them and restart the client. Codex only loads project settings from trusted projects. Permission profiles are beta; use a current client that supports `default_permissions`, named profiles, `extends`, and filesystem `deny` rules. The documented migration baseline is Codex 0.138.0; the local sandbox canary was tested with 0.159.2 on macOS (see validation notes).

## Input policy

Sensitive defaults (`.env`, `.env.*`, private-key and credential filename patterns) are always added. `.agentignore` is optional, hand-maintained, and never rewritten:

```gitignore
# Optional project-specific exclusions
/private-data/
node_modules/
dist/
*.log
```

The syntax is deliberately smaller than `.gitignore`:

- A basename like `.env` or `*.key` matches at any depth.
- `/private-data/` anchors at the project root; `private-data/` matches directory basenames at any depth.
- A path containing a slash, like `config/*.json`, is rooted at the project root.
- A trailing `/` expands to `/**`. `*`, `?`, and `**` are supported.
- Negation (`!`), character classes, escapes, parent traversal, whitespace and parentheses are rejected before writing either output. Do not copy a full `.gitignore` into this file.

`.gitignore` is **not automatically imported**. Version-control exclusions and agent access permissions serve different purposes. Artifact and lockfile exclusions can prevent useful debugging or dependency updates: choose them deliberately. `sync --include-lockfiles` adds lockfile deny rules explicitly.

The previous release generated `.claudeignore` and other vendor-named ignore files. These files do not count as permissions in 0.2. Migrate custom exclusions into the supported input syntax yourself; this release does not alter existing legacy files in your project.

## Safe synchronization

`sync` preflights both outputs before writing. It merges Claude deny entries while preserving existing model, environment, hooks and allow rules. Codex TOML comments and unrelated settings are preserved. Existing files receive a first-write `*.agentignore.bak` backup, and repeated syncs are idempotent. No home-directory or managed settings are modified.

Codex refuses to replace an existing selected profile or an unowned `agentignore` profile. Local legacy `sandbox_mode` / `sandbox_workspace_write` settings must be migrated explicitly; they take precedence over permission profiles. Inherited legacy settings and command-line overrides require your review too. Claude configurations using `bypassPermissions` are rejected.

Synchronization is additive: previously compiled deny rules remain if you remove a pattern from the input. Remove obsolete entries from each output manually after review. Do not use the generated profile for custom read/write exceptions: mixed overrides are rejected. Symlink settings files/directories are refused. Each output is replaced atomically; a filesystem failure between outputs can still leave a partial sync, so inspect errors and backups.

## Audit and reports

```sh
agentignore check --deep
agentignore check --export audit.json
agentignore check --export audit.md
agentignore --lang zh check
```

Checks report files with missing modeled project-local deny rules, optional artifact recommendations, secret signatures, and malformed/conflicting configuration. Exit codes: `0` no static findings, `1` findings, `2` invalid input or an operational error. `--no-strict` makes findings return `0`; input errors still return `2`.

Reports explicitly include `assessment: static_configuration_only`, `runtime_verified: false`, configuration errors, and limitations. `.agentignore` alone never clears findings. Deep secret findings remain visible even when a deny rule covers the source file; rotate/remove real exposed credentials rather than merely excluding source code.

The inspector models project-root-anchored Claude `Read(/...)` rules and Codex deny-only workspace tables extending a built-in profile. Unsupported inheritance or mixed Codex read/write overrides are reported as unknown rather than protected. Alternative Claude path forms do not count as coverage in this conservative checker. Existing policy files, VCS directories and `.codex` / `.claude` configuration directories are not scanned for file findings. Symlinks are reported but not followed. Deep scanning skips binary files, files over 1 MB, and lines over 5000 characters. For comprehensive secret detection, use a dedicated secret scanner.

## Verify the actual client

Use fake canaries, never production credentials. For Codex, create `.env.agentignore-canary` containing a harmless string and `agentignore-public-canary.txt` containing another string, then run from the project root:

```sh
codex sandbox -P agentignore -C . -- /bin/cat agentignore-public-canary.txt
codex sandbox -P agentignore -C . -- /bin/cat .env.agentignore-canary
```

The first command should succeed; the second should fail with a permission error. This explicitly selects the profile. Separately confirm that ordinary sessions load the intended default profile; explicit selection does not prove project trust or configuration precedence. Platform failures are not a passing security check. Delete canaries after testing.

For Claude Code, review `/permissions`, restart from the project root, and ask it to read the same fake secret through its built-in Read tool. Verify refusal. Read/Edit deny rules also cover recognized Bash file commands in current Claude versions, but do **not** cover arbitrary scripts that open files indirectly. For stronger command isolation, configure Claude's OS sandbox separately. This release does not change sandbox or MCP policies.

## Limits of enforcement

- Codex profiles govern sandboxed local commands. MCP, connectors, cloud environments, browser tools, and approved escalations have separate controls.
- Claude deny rules do not form an OS-level barrier for arbitrary subprocesses or MCP tools.
- User settings, managed policies, project trust, CLI overrides and bypass modes can change effective permissions.
- Codex deny globs may be expanded at sandbox startup on some platforms. The generated scan depth is 20; files beyond the supported expansion depth or created later require runtime verification.
- Files already included in chat, editor selections, environment variables, and external services are outside this scanner's assessment.

See the official [Codex permissions](https://developers.openai.com/codex/permissions/), [Codex configuration reference](https://developers.openai.com/codex/config-reference/), [Claude permissions](https://code.claude.com/docs/en/permissions), [Claude settings](https://code.claude.com/docs/en/settings), and [Claude sandbox](https://code.claude.com/docs/en/sandboxing) documentation. Configuration formats can change.

## Context estimates

```sh
agentignore cost --queries 100 --input-rate 3
```

This estimates a **hypothetical full-read scenario**, using flagged text bytes / 4 and your explicit USD price per million input tokens. It is not measured usage or savings. Actual reads, tokenization, cache discounts, subscriptions and billing vary. No provider pricing is hardcoded.

## Git hook

```sh
agentignore hook install
agentignore hook uninstall
```

The optional hook runs a working-tree static check. It is not a staged-index secret scanner and cannot guarantee secrets are never committed. Installation refuses to overwrite another tool's hook. Git worktree hook discovery and `core.hooksPath` are not supported in this release; integrate the CLI with your existing hook runner instead.

## 中文说明

agentignore 现在只针对 **Codex 和 Claude Code**，把统一的拒绝访问策略编译到真实配置中：

- Codex：`.codex/config.toml` 中的命名权限配置，限制本地沙箱命令。
- Claude Code：`.claude/settings.json` 中的 `Read` / `Edit` 拒绝规则。
- `.agentignore` 仅是输入文件，不会自动让任何客户端受到保护；检查通过也不代表零泄漏。

先运行 `sync --dry-run` 查看将变更的文件，再运行 `sync`。已有配置会合并并备份；模型设置和其他配置会保留。存在旧沙箱配置、其他已选权限配置或不支持的规则时，先报告冲突，不自动覆盖。

只支持路径、`*`、`?`、`**`，不支持 `!` 例外。默认加入敏感文件规则；构建产物、依赖目录和锁文件由你明确选择，不直接复制 `.gitignore`。拒绝规则是累加的，移除输入后需要手动审查并移除输出中的旧规则。

重启客户端，确认项目受信任和权限配置已加载，再用假密钥文件验证拒绝读取。Codex 的 MCP、云端及提权执行，Claude 的任意脚本和 MCP，不在这次配置的统一保护范围内。成本输出是明确假设下的估算，不是实测节省费用。

## Development

```sh
python -m pip install -e '.[dev]'
python -m pytest -q
```

MIT licensed. See [LICENSE](LICENSE).
