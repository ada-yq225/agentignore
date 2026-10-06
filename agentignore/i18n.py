"""Internationalization (i18n) support for agentignore: English and Chinese."""

import os
from typing import Any, Dict

DEFAULT_LANG = "en"


def detect_system_language() -> str:
    """Detect whether system language is Chinese or English."""
    env_lang = (
        os.environ.get("AGENTIGNORE_LANG")
        or os.environ.get("LC_ALL")
        or os.environ.get("LC_MESSAGES")
        or os.environ.get("LANG")
        or ""
    ).lower()
    if "zh" in env_lang or "chinese" in env_lang:
        return "zh"
    return "en"


MESSAGES: Dict[str, Dict[str, str]] = {
    "en": {
        "banner_tag": "Universal AI Context Shield & Ignore Compiler",
        "project_stacks": "Project Stacks",
        "files_scanned": "Files Scanned",
        "active_shields": "Active Shields",
        "all_clean_title": "✓ ALL CLEAN & SECURE!",
        "all_clean_msg1": "No credentials, private keys, or context bloat are exposed to your AI coding tools.",
        "all_clean_msg2": "Your repository context is optimized for token efficiency.",
        "leaks_detected_title": "⚠️  Context Leaks Detected ({count} items exposed to AI)",
        "col_severity": "Severity",
        "col_path": "File / Dir Path",
        "col_category": "Category",
        "col_exposed_to": "Exposed To",
        "col_tokens": "Tokens (Est.)",
        "col_cost": "Cost / 100 Qs",
        "critical_risk_title": "🚨 CRITICAL RISK",
        "critical_risk_msg": "{count} secret/credential files or leaked API keys exposed to AI context!",
        "token_waste_title": "⚡ Token Waste",
        "token_waste_msg": "~{tokens:,} unnecessary tokens read per query (~${cost:.2f} wasted per 100 queries on Claude/GPT-4o).",
        "recommendation": "👉 Recommendation: Run `agentignore sync` to auto-shield these files across all AI tools.",
        "sync_title": "🔄 Syncing AI Ignore Files",
        "sync_dry_title": "🔄 Dry-run Syncing AI Ignore Files",
        "col_target_file": "Target File",
        "col_status": "Status",
        "status_created": "Created",
        "status_updated": "Updated",
        "status_unchanged": "Unchanged (Up-to-date)",
        "sync_success": "✓ Sync completed successfully! All {count} AI tools are now synchronized.",
        "quick_audit": "Verifying with a quick audit...",
        "perfect_shield": "🎉 Perfect! 0 leaks remaining. Your repository is now fully shielded.",
        "notice_remaining": "Notice: {count} files still flagged. Run `agentignore check` for details.",
        "targets_title": "Supported AI Tools & Target Files ({count} tools)",
        "col_target_key": "Target Key",
        "col_tool_name": "Tool Name",
        "col_ignore_file": "Ignore File",
        "col_configured": "Configured Locally?",
        "col_description": "Description",
        "diff_title": "Rule Comparison: .gitignore vs AI Shields",
        "hook_installed": "✓ Git pre-commit hook successfully installed at {path}",
        "hook_uninstalled": "✓ Git pre-commit hook successfully removed from {path}",
        "deep_scan_banner": "🔍 Deep Content Secret Scanning enabled...",
        "content_leak_desc": "Hardcoded secret in file content ({secret_type})",
        "cost_report_title": "Estimated Context Dollar Cost Impact (per 100 AI Queries)",
    },
    "zh": {
        "banner_tag": "面向 AI 编程的统一忽略规则编译器与防泄露上下文护盾",
        "project_stacks": "技术栈识别",
        "files_scanned": "扫描文件数",
        "active_shields": "已生效护盾",
        "all_clean_title": "✓ 全部安全无漏洞！",
        "all_clean_msg1": "未发现任何泄露的敏感密钥、私钥或膨胀文件暴露给 AI 编程工具。",
        "all_clean_msg2": "你的仓库上下文已达到最佳 Token 吞吐与经济效率。",
        "leaks_detected_title": "⚠️  检测到上下文泄露 ({count} 个项目暴露于 AI 工具)",
        "col_severity": "严重程度",
        "col_path": "文件 / 目录路径",
        "col_category": "类别",
        "col_exposed_to": "未设防的 AI 工具",
        "col_tokens": "Token 预估",
        "col_cost": "百次对话成本",
        "critical_risk_title": "🚨 高危泄露风险",
        "critical_risk_msg": "发现 {count} 处机密密钥文件或硬编码 API Key 正直接暴露在 AI 上下文中！",
        "token_waste_title": "⚡ Token 冗余浪费",
        "token_waste_msg": "每轮提问多消耗 ~{tokens:,} 无用 Token（以 Claude 3.5/GPT-4o 计，每 100 次提问白白浪费约 ${cost:.2f}）。",
        "recommendation": "👉 建议操作：运行 `agentignore sync` 一键为所有 AI 工具打上上下文护盾。",
        "sync_title": "🔄 正在同步 AI 工具忽略规则",
        "sync_dry_title": "🔄 规则预演 (Dry-run)",
        "col_target_file": "目标配置文件",
        "col_status": "同步状态",
        "status_created": "新建并生效",
        "status_updated": "更新规则",
        "status_unchanged": "已是最新 (无需修改)",
        "sync_success": "✓ 同步成功！全部 {count} 种主流 AI 编程工具已完全对齐。",
        "quick_audit": "正在执行快速自愈复检...",
        "perfect_shield": "🎉 完美！剩余漏洞数 0。你的代码仓库已被全面保护。",
        "notice_remaining": "注意：尚有 {count} 项未排除文件。请运行 `agentignore check` 查看详情。",
        "targets_title": "支持的 AI 编程工具与配置文件 ({count} 款)",
        "col_target_key": "标识符",
        "col_tool_name": "工具名称",
        "col_ignore_file": "忽略配置文件",
        "col_configured": "本地已配置？",
        "col_description": "功能说明",
        "diff_title": "规则比对：.gitignore vs AI 护盾",
        "hook_installed": "✓ Git pre-commit 钩子已成功安装至 {path}",
        "hook_uninstalled": "✓ Git pre-commit 钩子已成功卸载: {path}",
        "deep_scan_banner": "🔍 已开启代码内容深度机密密钥扫描...",
        "content_leak_desc": "文件内硬编码机密 ({secret_type})",
        "cost_report_title": "预估上下文经济成本测算 (每 100 次提问)",
    },
}


class I18n:
    def __init__(self, lang: str = "en"):
        self.lang = lang if lang in MESSAGES else DEFAULT_LANG

    def t(self, key: str, **kwargs: Any) -> str:
        text = MESSAGES.get(self.lang, {}).get(key) or MESSAGES[DEFAULT_LANG].get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text


_global_i18n = I18n(detect_system_language())


def set_language(lang: str) -> None:
    global _global_i18n
    _global_i18n = I18n(lang)


def get_i18n() -> I18n:
    return _global_i18n


def t(key: str, **kwargs: Any) -> str:
    return _global_i18n.t(key, **kwargs)
