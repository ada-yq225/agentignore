"""Tests for Git pre-commit hook manager."""

from pathlib import Path
from agentignore.hooks import install_pre_commit_hook, uninstall_pre_commit_hook


def test_hook_install_requires_git_dir(tmp_path: Path):
    ok, msg = install_pre_commit_hook(tmp_path)
    assert ok is False
    assert "missing .git" in msg


def test_hook_install_and_uninstall_lifecycle(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    ok, path_str = install_pre_commit_hook(tmp_path)
    assert ok is True
    hook_file = Path(path_str)
    assert hook_file.exists()
    assert "agentignore check" in hook_file.read_text(encoding="utf-8")

    # Uninstall
    un_ok, un_msg = uninstall_pre_commit_hook(tmp_path)
    assert un_ok is True
    assert not hook_file.exists()
