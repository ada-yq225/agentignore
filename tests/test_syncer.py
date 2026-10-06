"""Tests for ignore file syncer, generator, and idempotency."""

from pathlib import Path

from agentignore.core import audit_repository
from agentignore.syncer import extract_custom_rules, sync_repository


class TestSyncer:
    """Deterministic tests for sync, generation, and idempotency."""

    def test_sync_generates_all_target_files(self, tmp_path: Path):
        (tmp_path / ".gitignore").write_text("build/\n*.log\n", encoding="utf-8")
        results = sync_repository(tmp_path, dry_run=False)

        expected_files = [
            ".cursorignore",
            ".claudeignore",
            ".clineignore",
            ".copilotignore",
            ".windsurfignore",
            ".agentignore",
        ]
        for filename in expected_files:
            target_path = tmp_path / filename
            assert target_path.exists(), f"Expected {filename} to be generated"
            assert results[filename] == "created"

            content = target_path.read_text(encoding="utf-8")
            # Verify sensitive shields are included
            assert ".env" in content
            assert "*.pem" in content
            # Verify gitignore mirrored rules are included
            assert "build/" in content

    def test_sync_idempotency(self, tmp_path: Path):
        """Running sync twice without repo changes must be completely unchanged."""
        first_results = sync_repository(tmp_path, dry_run=False)
        assert all(status == "created" for status in first_results.values())

        second_results = sync_repository(tmp_path, dry_run=False)
        assert all(status == "unchanged" for status in second_results.values())

    def test_custom_user_rules_are_preserved(self, tmp_path: Path):
        # First sync
        sync_repository(tmp_path, targets=["cursor"])
        cursor_file = tmp_path / ".cursorignore"

        # User appends a custom rule to .cursorignore
        custom_rule = "my_private_notebooks/"
        with open(cursor_file, "a", encoding="utf-8") as f:
            f.write(f"\n{custom_rule}\n")

        # Second sync
        sync_repository(tmp_path, targets=["cursor", "claude"])

        # Check that the custom rule is preserved in both files!
        cursor_content = cursor_file.read_text(encoding="utf-8")
        assert custom_rule in cursor_content

        claude_content = (tmp_path / ".claudeignore").read_text(encoding="utf-8")
        assert custom_rule in claude_content

    def test_end_to_end_self_healing_from_leaks(self, tmp_path: Path):
        """Verify that a repository with detected leaks becomes 100% clean after sync."""
        # Setup a repository with multiple leaks
        (tmp_path / ".env.production").write_text("API_SECRET=abc", encoding="utf-8")
        (tmp_path / "package.json").write_text('{"name": "demo"}', encoding="utf-8")

        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        (dist_dir / "bundle.js").write_text("var code = 1;", encoding="utf-8")

        # Initial audit should fail with leaks
        initial_report = audit_repository(tmp_path)
        assert initial_report.is_clean is False
        assert initial_report.critical_leaks_count >= 1

        # Run sync
        sync_results = sync_repository(tmp_path)
        assert sync_results[".cursorignore"] == "created"

        # Re-audit: must now be 100% clean!
        post_sync_report = audit_repository(tmp_path)
        assert post_sync_report.is_clean is True
        assert len(post_sync_report.leaks) == 0
        assert post_sync_report.critical_leaks_count == 0
