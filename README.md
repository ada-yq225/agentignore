<div align="center">

# 🛡️ agentignore

**The Universal AI Context Shield & Ignore Compiler**  
*Protect your secrets. Stop burning tokens. Unify your AI ignore files across 12+ coding assistants.*

[![Tests](https://img.shields.io/badge/tests-87%20passed-brightgreen?style=flat-square)](https://github.com/ada-yq225/agentignore)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg?style=flat-square)](https://pypi.org/project/agentignore/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Zero External API](https://img.shields.io/badge/100%25%20Offline-Zero%20API%20Required-success?style=flat-square)](https://github.com/ada-yq225/agentignore)
[![Tools Supported](https://img.shields.io/badge/AI%20Tools-12%20Supported-purple?style=flat-square)](https://github.com/ada-yq225/agentignore)

[English](#english) | [中文说明](#chinese)

</div>

---

<a name="english"></a>
## 💡 Why agentignore?

Every developer is now using AI coding assistants (**Cursor**, **Claude Code**, **Cline**, **GitHub Copilot**, **Windsurf**, **Aider**, etc.).

However, **there is a silent, costly crisis in AI programming**:
1. 🚨 **Secret Leaks**: In Cursor and Claude Code, `.gitignore` **only stops codebase search indexing**, but the AI agent can **still read `.env`, `.env.local`, and private keys** via internal tools! Without a dedicated ignore file, your production API keys may be sent directly to cloud LLMs.
2. 💸 **Massive Token Waste**: If build outputs (`dist/`, `node_modules/`, `target/`) or massive lockfiles (`pnpm-lock.yaml`) aren't explicitly shielded, agents burn **30,000 ~ 100,000 unnecessary tokens per query**, draining your wallet and hitting model context limits.
3. 🌀 **Extreme Ecosystem Fragmentation**: Every AI tool requires its own proprietary ignore file format:
   * **Cursor**: `.cursorignore`
   * **Claude Code**: `.claudeignore`
   * **Cline**: `.clineignore`
   * **GitHub Copilot**: `.copilotignore`
   * **Windsurf**: `.windsurfignore`
   * **JetBrains AI**: `.aiignore`
   * **Aider**: `.aiderignore`
   * **Continue.dev**: `.continueignore`
   * **Sourcegraph Cody**: `.codyignore`
   * **Gemini Code Assist**: `.geminiignore`
   * **OpenCode**: `.opencodeignore`
   * **Universal Standard**: `.agentignore`

**`agentignore` solves this completely.** It is a zero-config, 100% offline, deterministic CLI that audits your repo for AI context leaks, estimates monetary dollar waste, deep-scans for hardcoded secrets, and compiles unified shields across all 12 tools in milliseconds.

---

## ⚡ Quickstart

### Option A: Zero Install (Run instantly with `uvx` or `pipx`)
```bash
# Instant audit: 0 seconds install, runs completely offline
uvx agentignore check

# Or with pipx:
pipx run agentignore check
```

### Option B: Standard Installation
```bash
pip install agentignore
```

---

## 🖥️ Feature Highlights & Usage

### 1. Audit Your Repo (`agentignore check`)
Scan for exposed secrets, unshielded build artifacts, and token bloat:

```bash
agentignore check
```

#### Advanced Audit Flags:
```bash
# Deep scan file contents for leaked API keys (OpenAI, AWS, GitHub PATs, etc.)
agentignore check --deep

# Calculate estimated dollar waste per 100 queries on Claude 3.5 / GPT-4o
agentignore check --cost

# Export audit report to Markdown or JSON for team reviews / CI
agentignore check --export security-audit.md

# Switch language to Chinese or English
agentignore --lang zh check
```

#### Terminal Preview:
```text
🛡️  agentignore v0.1.0 — Universal AI Context Shield & Ignore Compiler

Project Stacks: Node.js / TypeScript, Python   Files Scanned: 42
Active Shields: ✗ .cursorignore ✗ .claudeignore ✗ .clineignore

⚠️  Context Leaks Detected (3 items exposed to AI)
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Severity ┃ File Path        ┃ Category    ┃ Exposed To                 ┃ Tokens (Est.)┃ Cost / 100 Q┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ CRITICAL │ .env.local       │ sensitive   │ .cursorignore, .claudeign… │           ~95│        $0.01│
│ HIGH     │ dist/            │ bloat       │ .cursorignore, .claudeign… │      ~845,000│       $25.35│
│ MEDIUM   │ pnpm-lock.yaml   │ lockfile    │ .cursorignore, .claudeign… │       ~48,200│        $1.45│
└━━━━━━━━━━┴━━━━━━━━━━━━━━━━━━┴━━━━━━━━━━━━━┴━━━━━━━━━━━━━━━━━━━━━━━━━━━━┴━━━━━━━━━━━━━━┴━━━━━━━━━━━━━┘

🚨 CRITICAL RISK: 1 secret/credential files exposed to AI context!
⚡ Token Waste: ~893,295 unnecessary tokens read per query (~$26.81 wasted per 100 queries on Claude/GPT-4o).

👉 Recommendation: Run `agentignore sync` to auto-shield these files across all AI tools.
```

---

### 2. Auto-Fix & Synchronize Across 12 AI Tools (`agentignore sync`)
One command to shield your repository across all AI assistants:

```bash
agentignore sync
```

```text
 🔄 Syncing AI Ignore Files  
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Target File     ┃ Status  ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ .cursorignore   │ Created │
│ .claudeignore   │ Created │
│ .clineignore    │ Created │
│ .copilotignore  │ Created │
│ .windsurfignore │ Created │
│ .aiignore       │ Created │
│ .aiderignore    │ Created │
│ .continueignore │ Created │
│ .codyignore     │ Created │
│ .geminiignore   │ Created │
│ .opencodeignore │ Created │
│ .agentignore    │ Created │
└─────────────────┴─────────┘

✓ Sync completed successfully! All 12 AI tools are now synchronized.
🎉 Perfect! 0 leaks remaining. Your repository is now fully shielded.
```

---

### 3. Compare Rules (`agentignore diff`)
Compare `.gitignore` with `.cursorignore` (or any tool) to see missing exclusions:
```bash
agentignore diff --target cursor
```

---

### 4. Dollar Waste Calculator (`agentignore cost`)
View a breakdown of financial waste across major model providers (Claude 3.5 Sonnet, GPT-4o, Gemini 1.5 Pro):
```bash
agentignore cost --queries 100
```

---

### 5. Automated Git Pre-commit Hook (`agentignore hook`)
Ensure secrets and bloat files can never be committed or indexed:
```bash
agentignore hook install
# Automatically blocks commits that leak credentials to AI tools!
```

---

## 🛡️ Supported AI Tools (12 Tools)

| Tool | Target File | Supported |
| :--- | :--- | :---: |
| **Cursor IDE** | `.cursorignore` | ✅ |
| **Claude Code (Anthropic)** | `.claudeignore` | ✅ |
| **Cline / Roo-Cline** | `.clineignore` | ✅ |
| **GitHub Copilot** | `.copilotignore` | ✅ |
| **Codeium Windsurf** | `.windsurfignore` | ✅ |
| **JetBrains AI Assistant** | `.aiignore` | ✅ |
| **Aider** | `.aiderignore` | ✅ |
| **Continue.dev** | `.continueignore` | ✅ |
| **Sourcegraph Cody** | `.codyignore` | ✅ |
| **Gemini Code Assist** | `.geminiignore` | ✅ |
| **OpenCode** | `.opencodeignore` | ✅ |
| **Universal Standard** | `.agentignore` | ✅ |

---

## 🔒 100% Deterministic & Verifiable

* **Zero External APIs**: 100% offline. No API key needed, zero network requests.
* **100% Test Coverage**: 87 passing automated tests covering glob edge cases, directory pruning, and regex signatures.
* **Idempotent**: Re-running `sync` preserves custom user rules and never produces duplicate lines.

---

<a name="chinese"></a>
## 🇨🇳 中文说明

### 解决的核心痛点
1. **真实密钥泄露风险**：在 Cursor 和 Claude Code 中，`.gitignore` 仅阻止全局检索，**AI Agent 依然可以通过读取工具访问 `.env` 和私钥**！必须配置专属的 ignore 文件。
2. **巨额 Token 浪费**：构建产物（`dist/`）、大型 Lockfile 未被忽略时，AI 每次对话都在后台读取这些垃圾文件，每轮提问白白浪费上万 Token 费用并导致编辑器卡顿。
3. **多工具配置碎片化**：各大 AI 工具（Cursor、Claude、Cline、Copilot、Aider、Windsurf 等）各自为政，难以统合维护。

### 功能清单
* 🌐 **原生中英双语支持**：通过 `--lang zh` 或自动检测系统环境，提供中文彩色终端界面。
* 🛡️ **覆盖 12 大主流 AI 工具**：一键生成与对齐 `.cursorignore`、`.claudeignore`、`.aiderignore` 等全部规则。
* 🔍 **深度机密内容扫描 (`--deep`)**：不仅检查文件名，还深度扫描文件内容中的 OpenAI、Anthropic、AWS、GitHub 泄露密钥。
* 💰 **经济成本测算 (`cost` / `--cost`)**：精确测算仓库冗余上下文在 Claude 3.5 Sonnet / GPT-4o 下造成的美元浪费。
* ⚖️ **规则比对 (`diff`)**：精确比对 `.gitignore` 与 AI 护盾文件的差集。
* 🪝 **Git 提交拦截器 (`hook install`)**：一键安装本地 Git pre-commit 钩子，从源头杜绝未设防文件提交。
* 📄 **审计报告导出 (`--export`)**：支持一键导出为 Markdown 或 JSON 报告，方便团队 PR 审查。

---

## 📄 License

MIT License. Open-source and free forever!
