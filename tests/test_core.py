"""Tests for core audit engine and ignore ruleset matching."""

from pathlib import Path
import pytest

from agentignore.core import IgnoreRuleSet, audit_repository


class TestIgnoreRuleSet:
    """Tests for the gitwildmatch-compliant IgnoreRuleSet."""

    def test_basic_matching(self):
        rules = IgnoreRuleSet(["node_modules/", "*.log", ".env*"])
        assert rules.matches("node_modules/pkg/index.js") is True
        assert rules.matches("app.log") is True
        assert rules.matches("logs/debug.log") is True
        assert rules.matches(".env.local") is True
        assert rules.matches("src/index.ts") is False

    def test_comment_and_blank_lines_ignored(self):
        rules = IgnoreRuleSet(["# This is a comment", "", "   ", "*.tmp"])
        assert rules.matches("file.tmp") is True
        assert rules.matches("file.txt") is False

    def test_negation_rules(self):
        rules = IgnoreRuleSet(["*.log", "!important.log"])
        assert rules.matches("debug.log") is True
        assert rules.matches("important.log") is False

    def test_load_from_file(self, tmp_path: Path):
        ignore_file = tmp_path / ".customignore"
        ignore_file.write_text("build/\n*.bak\n", encoding="utf-8")
        rules = IgnoreRuleSet.from_file(ignore_file)
        assert rules.matches("build/output.js") is True
        assert rules.matches("notes.bak") is True
        assert rules.matches("notes.txt") is False


class TestAuditRepository:
    """Deterministic integration tests for audit_repository."""

    def test_clean_repository_with_complete_shields(self, tmp_path: Path):
        # Create normal files
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
        (tmp_path / "README.md").write_text("# My Project", encoding="utf-8")

        # Create all target ignore files with proper rules
        shield_content = ".env*\n*.log\nnode_modules/\n"
        for fname in [".cursorignore", ".claudeignore", ".clineignore", ".copilotignore", ".windsurfignore"]:
            (tmp_path / fname).write_text(shield_content, encoding="utf-8")

        report = audit_repository(tmp_path)
        assert report.is_clean is True
        assert len(report.leaks) == 0
        assert report.critical_leaks_count == 0

    def test_detects_exposed_env_secret_file(self, tmp_path: Path):
        # Leaky scenario: .env exists, but no AI ignore files exist
        (tmp_path / ".env.local").write_text("DATABASE_URL=postgres://...", encoding="utf-8")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "index.js").write_text("console.log('hi');", encoding="utf-8")

        report = audit_repository(tmp_path)
        assert report.is_clean is False
        assert report.critical_leaks_count == 1

        env_leak = next(leak for leak in report.leaks if leak.path == ".env.local")
        assert env_leak.category == "sensitive"
        assert env_leak.severity == "CRITICAL"
        assert ".cursorignore" in env_leak.unshielded_targets
        assert ".claudeignore" in env_leak.unshielded_targets

    def test_detects_git_ignored_file_missing_in_cursorignore(self, tmp_path: Path):
        # .gitignore ignores dist/
        (tmp_path / ".gitignore").write_text("dist/\n", encoding="utf-8")
        (tmp_path / "dist").mkdir()
        (tmp_path / "dist" / "bundle.js").write_text("var x = 1;" * 500, encoding="utf-8")

        # Claude has .claudeignore, but Cursor has no .cursorignore
        (tmp_path / ".claudeignore").write_text("dist/\n", encoding="utf-8")

        report = audit_repository(tmp_path, target_names=["cursor", "claude"])
        assert report.is_clean is False

        dist_leak = next(leak for leak in report.leaks if "dist" in leak.path)
        # It should be flagged because .cursorignore does NOT shield it
        assert ".cursorignore" in dist_leak.unshielded_targets
        # But .claudeignore DOES shield it, so claude should not be in unshielded targets
        assert ".claudeignore" not in dist_leak.unshielded_targets

    def test_universal_agentignore_shields_unconfigured_targets(self, tmp_path: Path):
        # When .agentignore is present, it acts as a universal shield
        (tmp_path / ".agentignore").write_text(".env*\ndist/\n", encoding="utf-8")
        (tmp_path / ".env").write_text("SECRET=123", encoding="utf-8")
        (tmp_path / "dist").mkdir()
        (tmp_path / "dist" / "app.js").write_text("console.log(1);", encoding="utf-8")

        report = audit_repository(tmp_path)
        # Because .agentignore matches, no unshielded targets remain
        assert report.is_clean is True
        assert len(report.leaks) == 0
