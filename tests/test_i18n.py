"""Tests for internationalization module."""

from agentignore.i18n import I18n, set_language, t


def test_i18n_english_translations():
    i18n = I18n("en")
    assert "STATIC" in i18n.t("all_clean_title")
    assert "Files Scanned" in i18n.t("files_scanned")


def test_i18n_chinese_translations():
    i18n = I18n("zh")
    assert "安全" in i18n.t("all_clean_title")
    assert "扫描文件数" in i18n.t("files_scanned")


def test_i18n_format_params():
    i18n = I18n("en")
    msg = i18n.t("critical_risk_msg", count=5)
    assert "5 secret/credential files" in msg


def test_global_language_switching():
    set_language("zh")
    assert "技术栈" in t("project_stacks")
    set_language("en")
    assert "Project Stacks" in t("project_stacks")
