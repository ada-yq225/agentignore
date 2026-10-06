"""Export static reports without claiming runtime enforcement."""
import json
from pathlib import Path


def export_markdown_report(report_data: dict, output_path: Path) -> None:
    lines = ['# 🛡️ agentignore Audit Report', '',
             f'Repository: `{report_data.get("repo_path")}`', '',
             'Assessment: static project-local configuration only. Runtime enforcement is **not verified**.', '',
             f'No static findings: {report_data.get("is_clean")}',
             f'Files scanned: {report_data.get("scanned_files_count")}',
             f'Potential text context: ~{report_data.get("potential_context_tokens", 0):,} tokens (bytes / 4; not measured usage).', '',
             '## Configuration errors', '']
    lines += ['- ' + error for error in report_data.get('configuration_errors', [])]
    lines += ['', '## File findings', '', '| Severity | Path | Category | Missing deny config |', '| --- | --- | --- | --- |']
    for item in report_data.get('leaks', []):
        def cell(value):
            return str(value).replace('|', '\\|').replace('\n', ' ')
        lines.append('| ' + ' | '.join(cell(v) for v in (item['severity'], item['path'], item['category'], ', '.join(item['unshielded_targets']))) + ' |')
    lines += ['', '## Limits', '']
    lines += ['- ' + item for item in report_data.get('limitations', [])]
    output_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def export_json_report(report_data: dict, output_path: Path) -> None:
    output_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
