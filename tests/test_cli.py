"""Tests for the command-line interface and exit codes."""

import json
from pathlib import Path

from agentignore.cli import main


class TestCLI:
    """Deterministic tests for CLI commands and exit codes."""

    def test_cli_check_clean_repo_returns_exit_0(self, tmp_path: Path):
        (tmp_path / "README.md").write_text("# Hello", encoding="utf-8")
        # Initialize shields
        exit_code_sync = main(["sync", "--path", str(tmp_path)])
        assert exit_code_sync == 0

        exit_code_check = main(["check", "--path", str(tmp_path)])
        assert exit_code_check == 0

    def test_cli_check_leaky_repo_returns_exit_1_in_strict_mode(self, tmp_path: Path):
        # Create an unshielded secret file
        (tmp_path / ".env.local").write_text("SECRET=123", encoding="utf-8")

        exit_code_check = main(["check", "--path", str(tmp_path), "--strict"])
        assert exit_code_check == 1

    def test_cli_check_leaky_repo_returns_exit_0_when_no_strict(self, tmp_path: Path):
        (tmp_path / ".env.local").write_text("SECRET=123", encoding="utf-8")

        exit_code_check = main(["check", "--path", str(tmp_path), "--no-strict"])
        assert exit_code_check == 0

    def test_cli_json_output(self, tmp_path: Path, capsys):
        (tmp_path / ".env").write_text("KEY=abc", encoding="utf-8")

        exit_code = main(["check", "--path", str(tmp_path), "--json", "--no-strict"])
        assert exit_code == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["is_clean"] is False
        assert data["critical_leaks_count"] == 1
        assert len(data["leaks"]) >= 1

    def test_cli_targets_command(self, tmp_path: Path):
        exit_code = main(["targets", "--path", str(tmp_path)])
        assert exit_code == 0

    def test_cli_targets_chinese_language(self, tmp_path: Path):
        exit_code = main(["--lang", "zh", "targets", "--path", str(tmp_path)])
        assert exit_code == 0

    def test_cli_sync_dry_run(self, tmp_path: Path):
        (tmp_path / "index.js").write_text("console.log(1);", encoding="utf-8")
        exit_code = main(["sync", "--path", str(tmp_path), "--dry-run"])
        assert exit_code == 0
        assert not (tmp_path / ".codex").exists()

    def test_cli_diff_command(self, tmp_path: Path):
        (tmp_path / ".gitignore").write_text("dist/\n", encoding="utf-8")
        exit_code = main(["diff", "--path", str(tmp_path)])
        assert exit_code == 0

    def test_cli_cost_command(self, tmp_path: Path):
        (tmp_path / ".env").write_text("A" * 4000, encoding="utf-8")
        exit_code = main(["cost", "--path", str(tmp_path), "--queries", "50", "--input-rate", "3"])
        assert exit_code == 0

    def test_cli_hook_command(self, tmp_path: Path):
        (tmp_path / ".git").mkdir()
        exit_install = main(["hook", "install", "--path", str(tmp_path)])
        assert exit_install == 0
        exit_uninstall = main(["hook", "uninstall", "--path", str(tmp_path)])
        assert exit_uninstall == 0

    def test_cli_check_with_export_and_deep_scan(self, tmp_path: Path):
        export_file = tmp_path / "audit.md"
        (tmp_path / "app.py").write_text('API_KEY = "sk-proj-1234567890abcdef1234567890"', encoding="utf-8")
        exit_code = main(["check", "--path", str(tmp_path), "--deep", "--export", str(export_file), "--no-strict"])
        assert exit_code == 0
        assert export_file.exists()
        assert "agentignore Audit Report" in export_file.read_text(encoding="utf-8")


def test_unknown_cli_target_fails(tmp_path):
    assert main(['sync', '--path', str(tmp_path), '--targets', 'codex,typo']) == 2
    assert not (tmp_path / '.codex').exists()


def test_json_invalid_configuration_is_parseable(tmp_path, capsys):
    (tmp_path / '.agentignore').write_text('!exception')
    assert main(['check', '--path', str(tmp_path), '--json']) == 2
    assert 'error' in json.loads(capsys.readouterr().out)
