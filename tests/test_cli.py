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

    def test_cli_sync_dry_run(self, tmp_path: Path):
        (tmp_path / "index.js").write_text("console.log(1);", encoding="utf-8")
        exit_code = main(["sync", "--path", str(tmp_path), "--dry-run"])
        assert exit_code == 0
        # In dry run, files should not be written to disk
        assert not (tmp_path / ".cursorignore").exists()
