"""Tests for report exporter module."""

import json
from pathlib import Path
from agentignore.exporter import export_json_report, export_markdown_report


def test_export_markdown_report(tmp_path: Path):
    md_file = tmp_path / "report.md"
    data = {
        "repo_path": "/test/repo",
        "is_clean": False,
        "scanned_files_count": 10,
        "critical_leaks_count": 1,
        "potential_context_tokens": 5000,
        "leaks": [
            {
                "path": ".env",
                "severity": "CRITICAL",
                "category": "sensitive",
                "unshielded_targets": [".claude/settings.json"],
                "estimated_tokens": 100,
            }
        ],
    }
    export_markdown_report(data, md_file)
    assert md_file.exists()
    content = md_file.read_text(encoding="utf-8")
    assert "# 🛡️ agentignore Audit Report" in content
    assert ".env" in content
    assert "CRITICAL" in content


def test_export_json_report(tmp_path: Path):
    json_file = tmp_path / "report.json"
    data = {"status": "ok", "leaks": []}
    export_json_report(data, json_file)
    assert json_file.exists()
    loaded = json.loads(json_file.read_text(encoding="utf-8"))
    assert loaded["status"] == "ok"
