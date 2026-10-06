"""Export audit reports to Markdown, JSON, and HTML formats."""

import json
from pathlib import Path
from typing import Any, Dict

from agentignore.cost import estimate_dollar_cost


def export_markdown_report(report_data: Dict[str, Any], output_path: Path) -> None:
    """Export audit report as a clean GitHub-flavored Markdown file."""
    lines = [
        "# 🛡️ agentignore Audit Report",
        "",
        f"- **Repository:** `{report_data.get('repo_path')}`",
        f"- **Status:** {'✅ Clean (Protected)' if report_data.get('is_clean') else '⚠️ Leaks Detected'}",
        f"- **Files Scanned:** {report_data.get('scanned_files_count')}",
        f"- **Critical Secrets Exposed:** {report_data.get('critical_leaks_count')}",
        f"- **Estimated Token Waste:** {report_data.get('total_wasted_tokens', 0):,} tokens/query",
        "",
    ]

    leaks = report_data.get("leaks", [])
    if leaks:
        lines.append("## ⚠️ Detected Leaks")
        lines.append("")
        lines.append("| Severity | Path | Category | Exposed To | Est. Tokens |")
        lines.append("| :--- | :--- | :--- | :--- | :---: |")
        for leak in leaks:
            exposed = ", ".join(leak.get("unshielded_targets", []))
            lines.append(
                f"| **{leak.get('severity')}** | `{leak.get('path')}` | {leak.get('category')} | {exposed} | ~{leak.get('estimated_tokens', 0):,} |"
            )
        lines.append("")
        lines.append("> 💡 **Remediation:** Run `agentignore sync` to automatically shield these paths across all AI tools.")
    else:
        lines.append("## ✅ All Clean")
        lines.append("No sensitive files or token bloat are exposed to any supported AI tools.")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_json_report(report_data: Dict[str, Any], output_path: Path) -> None:
    """Export audit report as a JSON file."""
    output_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
