"""Tests for ignore diff engine."""

from pathlib import Path
from agentignore.syncer import compute_ignore_diff


def test_compute_ignore_diff(tmp_path: Path):
    # .gitignore has two rules
    (tmp_path / ".gitignore").write_text("dist/\nbuild/\n*.log\n", encoding="utf-8")
    # .cursorignore only has dist/
    (tmp_path / ".cursorignore").write_text("dist/\ncustom_rule/\n", encoding="utf-8")

    diff_data = compute_ignore_diff(tmp_path, target_key="cursor")
    assert "build/" in diff_data["missing_in_ai"]
    assert "*.log" in diff_data["missing_in_ai"]
    assert "dist/" not in diff_data["missing_in_ai"]
    assert "custom_rule/" in diff_data["unique_in_ai"]
