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
    'en': {
        'all_clean_title': 'NO STATIC FINDINGS',
        'files_scanned': 'Files Scanned',
        'project_stacks': 'Project Stacks',
        'critical_risk_msg': '{count} secret/credential files flagged; runtime exposure is not verified.',
    },
    'zh': {
        'all_clean_title': '未发现静态问题（不代表安全保证）',
        'files_scanned': '扫描文件数',
        'project_stacks': '技术栈识别',
        'critical_risk_msg': '发现 {count} 个敏感文件风险，未验证实际访问限制。',
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
