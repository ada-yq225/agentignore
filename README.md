# agentignore

**永久免费、MIT 开源，只为个人开发者的 Codex 项目提供本地权限配置与检查。**

把敏感文件、无需加入上下文的产物目录整理成一份策略，预览后编译到项目 `.codex/config.toml`。所有功能免费，无账号、订阅、付费版本或源代码上传。当前版本：**0.4.0**。

它检查项目里的静态配置；检查通过不代表 Codex 的实际会话已加载权限，也不保证零泄露。

## 三分钟开始

```bash
pip install .
cd /path/to/your/project
agentignore policy init --preset secrets
agentignore sync --dry-run --diff
agentignore sync
agentignore doctor
agentignore check --deep --export /tmp/agentignore-report.html
```

重启 Codex，确认项目受信任、配置已加载。在 macOS 上，可用以下命令验证一个公开文件能读取、一个假 `.env` 文件被拒绝；不会调用模型或使用真实密钥：

```bash
agentignore verify --json
```

自动验证目前只支持 macOS 上显式选定的本地权限 profile。其他平台和普通会话的有效权限仍须验证。请先用无敏感内容的测试项目尝试配置。

手动检查时，在已同步且受信任的测试项目中创建内容为 `DEMO_ONLY` 的 `.env.agentignore-canary` 和普通 `public.txt`。分别运行 `codex sandbox -P agentignore -- /bin/cat public.txt` 和 `codex sandbox -P agentignore -- /bin/cat .env.agentignore-canary`：前者应可读取，后者应收到权限拒绝且不输出文件内容。如果平台不支持此沙箱命令或测试失败，请将运行时状态视为未验证，不要据此处理真实密钥。

## 模板与项目设置

- `secrets`：拒绝常见环境文件、私钥和凭据文件名。
- `balanced`：在 secrets 基础上，加上 `node_modules`、虚拟环境、构建产物和覆盖率目录。确认 Codex 不需要访问这些文件后再使用。

`.agentignore.toml` 可编辑；未知键、非法类型、无效模式会明确报错：

```toml
version = 1

[project]
name = "My weekend project"
targets = ["codex"]

[policy]
preset = "secrets"
deny = ["/internal/", "*.dump"]

[check]
fail_on = "high"
```

```bash
agentignore policy show
```

也可在 `.agentignore` 中每行写一个拒绝模式。敏感文件默认规则始终加入；`.gitignore` 不会自动导入。支持项目相对路径、`*`、`?`、`**`、末尾 `/` 和以 `/` 开头的根目录模式。无 `/` 的文件名匹配任意深度；`/private/` 匹配根目录，`private/` 匹配任意深度目录。

不支持 `!` 反选、`[]` 字符集、空白、转义、括号、绝对路径或 `..`。这是明确的拒绝策略子集，不是完整 gitignore 语法。锁文件默认仅作为建议，可用 `sync --include-lockfiles` 明确加入拒绝策略。

## 安全预览、合并与恢复

```bash
agentignore sync --dry-run --diff
agentignore sync --dry-run --json
agentignore diff
```

预览只列出新增权限条目，不打印模型、环境变量等私有配置值。同步保留 TOML 注释和无关设置，只管理 `agentignore` 权限 profile；不会修改用户主目录配置。首次修改已有配置时保存 `config.toml.agentignore.bak`，重复同步保持幂等。新配置使用私有文件权限；更新保留原文件权限。

编译器拒绝替换其他已选 profile、未带所有权标记的同名 profile、符号链接配置和备份。已有 `sandbox_mode` / `sandbox_workspace_write` 必须先明确迁移，因为旧设置会影响权限 profile。

同步是**追加式**的：从输入删除模式不会自动撤销现有拒绝规则，避免无意扩大访问。需要回到首次同步前的已有配置时：

```bash
agentignore restore --dry-run --json
agentignore restore
```

恢复会替换当前受 agentignore 管理的配置，并将当前配置保存为 `config.toml.agentignore.before-restore.bak`，原始备份仍保留。恢复后重启 Codex 并检查权限。没有原始备份的新建配置不会自动删除；存在恢复快照、异常备份或临时文件时会停止，让你先检查文件。

## 报告与风险阈值

```bash
agentignore check --deep --export /tmp/agentignore-report.html
agentignore check --json
agentignore check --format sarif --export /tmp/agentignore-report.sarif
agentignore check --export /tmp/agentignore-report.md
```

HTML 报告离线运行，可搜索路径、筛选风险级别，包含修复建议。JSON 包含版本、稳定 finding ID 和阈值结果；SARIF 支持标准工具集成。报告不嵌入源码或完整凭据，但文件名和脱敏片段仍可能敏感，分享前请检查。

| 风险 | 默认行为 |
| --- | --- |
| CRITICAL：敏感文件缺少拒绝规则、疑似硬编码密钥 | 阻止检查通过 |
| HIGH：显式策略未配置到 Codex | 阻止检查通过 |
| MEDIUM：生成文件、锁文件等建议 | 显示建议，不阻止默认检查 |
| 配置或文件扫描错误 | 阻止检查通过 |

`--fail-on medium` 可提高检查严格程度，`--no-strict` 只改变退出状态。JSON 的 `is_clean` 表示没有发现或错误，`gate_failed` 表示选定阈值是否失败，两者含义不同。退出码：0 达到所选阈值，1 阈值未通过，2 输入或操作错误。

低/中风险建议可明确确认，必须给理由和最多 90 天的有效期；发现仍保留在报告中，高风险、严重风险和配置错误无法隐藏：

```bash
agentignore baseline create --reason "Required for dependency updates" --expires YYYY-MM-DD
agentignore check --fail-on medium --baseline .agentignore-baseline.json
```

`YYYY-MM-DD` 请替换为今天起 90 天内的日期。未显式传入 `--baseline` 时不会应用确认记录。

## Codex 权限边界

输出为命名的 `agentignore` profile，默认继承 `:workspace`，在 `filesystem.:workspace_roots` 中加入 deny 规则。权限 profiles 仍是 beta，格式和平台行为可能变化。

- 只有受沙箱约束的本地命令在本次配置范围内；MCP、连接器、云端任务和获准提权有独立控制。
- 项目信任、用户/托管配置、命令行覆盖和旧沙箱设置都可能改变实际权限。
- 静态检查保守建模直接继承内置 profile 的 deny-only 工作区规则；未知继承或混合 read/write 覆盖会报错。
- 扫描跳过 VCS 和 `.codex` 配置目录，不跟随符号链接。深度扫描跳过二进制、超过 1 MB 的文件和超过 5000 字符的行，并非完整秘密扫描器。
- canary 通过只证明显式 profile 对公开文件和假环境文件的当前观察结果，不证明所有路径、其他平台或普通会话。

参见官方 [Codex permissions](https://developers.openai.com/codex/permissions/) 与 [Codex configuration reference](https://developers.openai.com/codex/config-reference/)。

## 从 0.3 升级

0.4 起仅支持 Codex。已有 `.agentignore.toml` 中的 `project.targets` 改为 `["codex"]`。`--targets claude` 会明确报错；旧的其他客户端文件会保留，不读取、不修改或删除。若曾用旧版生成 vendor ignore 文件，它们不计为 Codex 权限；请将自定义模式移入上述策略输入。

JSON 中保留 targets 相关字段，兼容已有消费方，但唯一支持的目标是 Codex。

## 开发与开源

```bash
pip install -e '.[dev]'
python -m pytest -q
# macOS 上已安装 Codex CLI 时，可启用实际沙箱测试：
AGENTIGNORE_RUN_CODEX_CANARY=1 python -m pytest -q
```

贡献流程见 [CONTRIBUTING.md](CONTRIBUTING.md)，项目方向见 [PRODUCT.md](PRODUCT.md)，当前验证范围见 [VALIDATION.md](VALIDATION.md)。MIT 许可证允许自由使用、修改和再分发；本项目所有功能永久免费，不提供付费分层。

## English

agentignore is permanently free, MIT open source, local-first and **Codex only**. It compiles project deny rules into `.codex/config.toml`, offers safe previews and backup restoration, produces offline reports, and provides a macOS fake-secret canary. There is no account, subscription, paid tier or telemetry. Static coverage is not proof of runtime enforcement. Version 0.3 projects must change `project.targets` to `["codex"]`; unrelated client files remain untouched.
