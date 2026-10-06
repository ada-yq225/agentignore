<div align="center">

# 🛡️ agentignore

**The Universal AI Context Shield & Ignore Compiler**  
*Protect your secrets. Stop burning tokens. Unify your AI ignore files across all coding assistants.*

[![Tests](https://img.shields.io/badge/tests-66%20passed-brightgreen?style=flat-square)](https://github.com/ada-yq225/agentignore)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg?style=flat-square)](https://pypi.org/project/agentignore/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Zero External API](https://img.shields.io/badge/100%25%20Offline-Zero%20API%20Required-success?style=flat-square)](https://github.com/ada-yq225/agentignore)

[English](#english) | [中文说明](#chinese)

</div>

---

<a name="english"></a>
## 💡 Why agentignore?

Every developer is now using AI coding assistants (**Cursor**, **Claude Code**, **Cline**, **GitHub Copilot**, **Windsurf**). 

However, **there is a silent, costly problem**:
1. 🚨 **Secret Leaks**: Did you know that in Cursor and Claude Code, `.gitignore` **only stops indexing**, but the AI agent can **still read `.env` and `.env.local`** via its internal file-reading tools? Without a dedicated ignore file, your secrets may be sent directly to cloud LLMs.
2. 💸 **Massive Token Waste**: If build outputs (`dist/`, `node_modules/`, `target/`) or massive lockfiles (`pnpm-lock.yaml`) aren't explicitly shielded from AI tools, agents can burn **30,000 ~ 100,000 unnecessary tokens per interaction**, draining your wallet and hitting rate limits.
3. 🌀 **Ecosystem Fragmentation**: Every AI tool requires its own proprietary ignore file:
   * **Cursor**: `.cursorignore`
   * **Claude Code**: `.claudeignore`
   * **Cline**: `.clineignore`
   * **GitHub Copilot**: `.copilotignore`
   * **Windsurf**: `.windsurfignore`
   * **JetBrains AI**: `.aiignore`

**`agentignore` solves this completely.** It's a zero-config, 100% offline, deterministic CLI that audits your repo for AI context leaks and idempotently compiles unified shields across all your tools.

---

## ⚡ Quickstart

### Option A: Zero Install (Run instantly with `uvx` or `pipx`)
```bash
# Instant audit: 0 seconds install, runs locally
uvx agentignore check

# Or with pipx:
pipx run agentignore check
```

### Option B: Standard Installation
```bash
pip install agentignore
```

---

## 🖥️ Usage

### 1. Audit Your Repo (`agentignore check`)
Run in any repository root to scan for exposed secrets and context bloat:

```bash
agentignore check
```

#### Terminal Output:
```text
🛡️  agentignore v0.1.0 — Universal AI Context Shield & Ignore Compiler

Project Stacks: Node.js / TypeScript, Python   Files Scanned: 42
Active Shields: ✗ .cursorignore ✗ .claudeignore ✗ .clineignore

⚠️  Context Leaks Detected (3 items exposed to AI)
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Severity ┃ File Path        ┃ Category    ┃ Exposed To                 ┃ Tokens (Est.)┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ CRITICAL │ .env.local       │ sensitive   │ .cursorignore, .claudeign… │           ~95│
│ HIGH     │ dist/            │ bloat       │ .cursorignore, .claudeign… │      ~845,000│
│ MEDIUM   │ pnpm-lock.yaml   │ lockfile    │ .cursorignore, .claudeign… │       ~48,200│
└━━━━━━━━━━┴━━━━━━━━━━━━━━━━━━┴━━━━━━━━━━━━━┴━━━━━━━━━━━━━━━━━━━━━━━━━━━━┴━━━━━━━━━━━━━━┘

🚨 CRITICAL RISK: 1 secret/credential files exposed to AI tools!
⚡ Token Waste: ~893,295 unnecessary tokens being read per query.

👉 Recommendation: Run `agentignore sync` to auto-shield these files across all AI tools.
```

---

### 2. Auto-Fix & Synchronize (`agentignore sync`)
One command to shield your repo across all AI tools:

```bash
agentignore sync
```

```text
🛡️  agentignore v0.1.0 — Universal AI Context Shield & Ignore Compiler

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
│ .agentignore    │ Created │
└─────────────────┴─────────┘

✓ Sync completed successfully! All AI tools are now synchronized.
🎉 Perfect! 0 leaks remaining. Your repository is now fully shielded.
```

---

## 🔒 100% Deterministic & Verifiable

`agentignore` is built on mathematical boolean set logic using official Git RFC path specification algorithms (`pathspec`).
* **Zero External APIs**: No OpenAI, Anthropic, or cloud dependencies. Runs completely offline.
* **100% Test Coverage**: Tested across 66+ automated test cases covering glob edge cases, negation rules, and stack heuristics.
* **Idempotent**: Running `agentignore sync` multiple times never corrupts or duplicates rules. Custom user rules outside generated blocks are preserved automatically.

---

## 🛡️ Supported Tools

| Tool | Target File | Supported |
| :--- | :--- | :---: |
| **Cursor IDE** | `.cursorignore` | ✅ |
| **Claude Code (Anthropic)** | `.claudeignore` | ✅ |
| **Cline / Roo-Cline** | `.clineignore` | ✅ |
| **GitHub Copilot** | `.copilotignore` | ✅ |
| **Codeium Windsurf** | `.windsurfignore` | ✅ |
| **JetBrains AI Assistant** | `.aiignore` | ✅ |
| **Universal Standard** | `.agentignore` | ✅ |

---

## 🤖 CI/CD Integration

Block pull requests that accidentally expose secrets or heavy bloat to AI tools:

```yaml
# .github/workflows/ai-shield.yml
name: AI Context Shield Audit

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install agentignore
      - run: agentignore check --strict
```

---

<a name="chinese"></a>
## 🇨🇳 中文说明

### 解决的核心痛点
1. **真实密钥泄露风险**：在 Cursor 和 Claude Code 中，`.gitignore` 仅阻止全局检索，**AI Agent 依然可以通过读取工具访问 `.env` 和私钥**！必须配置专属的 ignore 文件。
2. **巨额 Token 浪费**：构建产物（`dist/`）、大型 Lockfile（数万行）未被忽略时，AI 每次对话都在后台读取这些垃圾文件，白白消耗巨量 Token 费用并导致编辑器卡顿。
3. **多工具配置碎片化**：Cursor (`.cursorignore`)、Claude Code (`.claudeignore`)、Cline (`.clineignore`) 各自为政，难以统合维护。

### 特性
* **纯本地 0 API 依赖**：100% 离线运行，毫秒级响应，无需网络与 API Key。
* **100% 客观可验证**：采用与 Git 官方底层相同的 `pathspec` 路径集合运算，非真即假，零玄学预测。
* **一键同步与自愈**：一键生成/同步所有 AI 工具规则，自动保留用户自定义配置，并杜绝重复配置。

---

## 📄 License

MIT License. Contributions, issues, and PRs are welcome!
