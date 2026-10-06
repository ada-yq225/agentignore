"""A complete local workflow: onboard, diagnose, preview, audit and report."""
import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.text import Text
from agentignore import __version__
from agentignore.adapters import LIMITATIONS
from agentignore.baseline import BASELINE_FILE, apply_baseline, create_baseline
from agentignore.constants import SUPPORTED_TARGETS
from agentignore.core import audit_repository
from agentignore.cost import estimate_dollar_cost
from agentignore.doctor import diagnose
from agentignore.exporter import export_json_report, export_markdown_report
from agentignore.reports import export_html_report, export_sarif_report, sarif_report
from agentignore.hooks import install_pre_commit_hook, uninstall_pre_commit_hook
from agentignore.i18n import detect_system_language
from agentignore.project import PRESETS, SEVERITIES, initialize_settings, load_settings
from agentignore.syncer import compute_ignore_diff, plan_repository, sync_repository, validate_targets

console = Console()


def _output(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _export(data, path, format=None):
    formats = {'.json': 'json', '.sarif': 'sarif', '.html': 'html', '.md': 'markdown'}
    format = format or formats.get(path.suffix.lower())
    writers = {'json': export_json_report, 'sarif': export_sarif_report,
               'html': export_html_report, 'markdown': export_markdown_report}
    if format not in writers:
        raise ValueError('Use .json, .sarif, .html or .md, or specify --format')
    writers[format](data, path)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog='agentignore', description='Local privacy and context controls for your Codex and Claude projects')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--lang', choices=['en', 'zh'], default=None)
    commands = parser.add_subparsers(dest='command')
    for command in ('check', 'audit', 'sync', 'init', 'diff', 'targets', 'cost', 'hook', 'policy', 'doctor', 'baseline', 'verify'):
        sub = commands.add_parser(command)
        sub.add_argument('--path', '-p', default='.')
        if command in ('check', 'audit', 'sync', 'init', 'policy', 'doctor', 'baseline', 'verify'):
            sub.add_argument('--targets', '-t', help='codex,claude (default: project settings)')
        if command in ('check', 'audit', 'sync', 'init', 'policy', 'doctor', 'verify'):
            sub.add_argument('--json', action='store_true')
        if command in ('check', 'audit'):
            sub.add_argument('--strict', action='store_true', default=True)
            sub.add_argument('--no-strict', dest='strict', action='store_false')
            sub.add_argument('--export')
            sub.add_argument('--format', choices=['json', 'sarif', 'html', 'markdown'])
            sub.add_argument('--deep', action='store_true')
            sub.add_argument('--ignore-lockfiles', action='store_true')
            sub.add_argument('--fail-on', choices=list(SEVERITIES))
            sub.add_argument('--baseline', help='Explicit baseline file; no automatic suppression')
        if command in ('sync', 'init'):
            sub.add_argument('--dry-run', action='store_true')
            sub.add_argument('--diff', action='store_true', help='Show added permission rules only, not private config values')
            sub.add_argument('--include-lockfiles', action='store_true')
        if command == 'policy':
            sub.add_argument('action', choices=['init', 'show'])
            sub.add_argument('--preset', choices=list(PRESETS), default='secrets')
            sub.add_argument('--name')
            sub.add_argument('--dry-run', action='store_true')
        if command == 'baseline':
            sub.add_argument('action', choices=['create'])
            sub.add_argument('--output', default=BASELINE_FILE)
            sub.add_argument('--reason', required=True)
            sub.add_argument('--expires', required=True, help='YYYY-MM-DD within 90 days')
        if command == 'verify':
            sub.add_argument('--target', choices=['codex'], default='codex')
        if command == 'diff':
            sub.add_argument('--target', choices=list(SUPPORTED_TARGETS), default='codex')
        if command == 'cost':
            sub.add_argument('--queries', type=int, default=100)
            sub.add_argument('--input-rate', type=float, required=True)
        if command == 'hook':
            sub.add_argument('action', choices=['install', 'uninstall'])
    args = parser.parse_args(argv)
    if args.command is None:
        return main(['--lang', args.lang or detect_system_language(), 'check'])
    zh = (args.lang or detect_system_language()) == 'zh'
    root = Path(args.path).resolve()
    try:
        if not root.is_dir():
            raise ValueError(f'Not a directory: {root}')
        settings = load_settings(root)
        explicit_targets = [x.strip() for x in args.targets.split(',')] if getattr(args, 'targets', None) else None
        targets = validate_targets(explicit_targets if explicit_targets is not None else settings.targets)
        if args.command in ('check', 'audit'):
            if args.json and args.format not in (None, 'json'):
                raise ValueError('--json cannot be combined with a different --format')
            if args.format in ('html', 'markdown') and not args.export:
                raise ValueError('HTML and Markdown require --export')
            report = audit_repository(root, targets, not args.ignore_lockfiles, args.deep)
            report.fail_on = args.fail_on or settings.fail_on
            if args.baseline:
                apply_baseline(report, Path(args.baseline).resolve())
            data = dict(version=__version__, **report.to_dict())
            if args.export:
                _export(data, Path(args.export), args.format)
            if args.json or args.format == 'json':
                _output(data)
            elif args.format == 'sarif':
                _output(sarif_report(data))
            else:
                console.print('个人项目体检 · 静态配置检查' if zh else 'Personal project check · Static configuration assessment')
                console.print(f'{settings.name} · {len(report.leaks)} findings · threshold: {report.fail_on}', markup=False)
                for error in report.configuration_errors:
                    console.print(error, style='red', markup=False)
                table = Table('Severity', 'Path', 'Category', 'Missing config', 'Status')
                for item in report.leaks:
                    table.add_row(Text(item.severity), Text(item.path), Text(item.category),
                                  Text(', '.join(item.unshielded_targets)), 'Acknowledged' if item.accepted else 'Review')
                console.print(table)
                console.print('检查阈值未通过，请查看修复建议。' if zh and report.gate_failed() else
                              'Threshold check failed; review the remediation steps.' if report.gate_failed() else
                              '达到检查阈值；不代表零风险或运行时已验证。' if zh else
                              'Threshold check passed; runtime enforcement remains unverified.')
                if report.leaks:
                    console.print(report.leaks[0].remediation, markup=False)
                if args.export:
                    console.print(f'Report: {args.export}', markup=False)
                console.print('No uploads. Full assessment limits are included in JSON and exported reports.', style='dim')
            return 1 if args.strict and report.gate_failed() else 0
        if args.command in ('sync', 'init'):
            plan = plan_repository(root, targets, include_lockfiles=args.include_lockfiles)
            if not args.dry_run:
                sync_repository(root, targets, include_lockfiles=args.include_lockfiles)
            if args.json:
                _output(dict(dry_run=args.dry_run, runtime_verified=False, changes=[item.summary(root) for item in plan]))
            else:
                for item in plan:
                    console.print(f'{item.path.relative_to(root)}: {item.status} · {len(item.added_permissions)} permission entries added' + (' (preview)' if args.dry_run else ''), markup=False)
                    if args.diff:
                        for rule in item.added_permissions:
                            console.print('+ ' + rule, markup=False)
                console.print('Review settings, restart the client, and verify a fake canary. Codex project config requires trust.')
            return 0
        if args.command == 'policy':
            if args.action == 'init':
                text = initialize_settings(root, args.preset, targets, args.name, args.dry_run)
                if args.json:
                    _output(dict(path='.agentignore.toml', dry_run=args.dry_run, content=text))
                else:
                    console.print(text, markup=False)
                    console.print('Next: agentignore sync --dry-run --diff')
            else:
                from agentignore.policy import read_policy
                _output(dict(version=1, settings=settings.to_dict(), effective_patterns=read_policy(root)))
            return 0
        if args.command == 'doctor':
            data = diagnose(root, targets)
            if args.json:
                _output(data)
            else:
                for item in data['clients']:
                    console.print(f'{item["target"]}: installed={item["installed"]} · version={item["version"] or "unknown"} · modeled config={item["config_valid"]}', markup=False)
                    if item['error']:
                        console.print(item['error'], style='yellow', markup=False)
                    console.print(item['next_step'], markup=False)
            return 0 if all(item['installed'] and item['config_valid'] for item in data['clients']) else 1
        if args.command == 'verify':
            from agentignore.verify import verify_codex
            data = verify_codex(root)
            if args.json:
                _output(data)
            else:
                console.print('Codex canary passed' if data['passed'] else 'Codex canary failed')
                console.print('Scope: explicit profile, fake .env, macOS. Ordinary sessions and other paths remain unverified.')
            return 0 if data['passed'] else 1
        if args.command == 'baseline':
            report = audit_repository(root, targets)
            output = Path(args.output)
            if not output.is_absolute():
                output = root / output
            data = create_baseline(report, output, args.reason, args.expires)
            console.print(f'{len(data["entries"])} low/medium findings acknowledged in {output}. High/critical findings and configuration errors remain blocking.', markup=False)
            return 0
        if args.command == 'diff':
            _output(compute_ignore_diff(root, args.target))
            return 0
        if args.command == 'targets':
            for key, info in SUPPORTED_TARGETS.items():
                console.print(f'{key}: {info["filename"]} — {info["description"]}', markup=False)
            return 0
        if args.command == 'cost':
            tokens = audit_repository(root).potential_context_tokens
            value = estimate_dollar_cost(tokens, args.queries, input_rate=args.input_rate)
            console.print(f'Hypothetical full-read scenario: ~{tokens:,} potential tokens × {args.queries} reads = ${value:.2f}.')
            console.print('Not measured savings. Assumes all flagged text is read in full on every request, without caching.')
            return 0
        if args.command == 'hook':
            ok, message = (install_pre_commit_hook if args.action == 'install' else uninstall_pre_commit_hook)(root)
            console.print(message, markup=False)
            return 0 if ok else 1
    except (ValueError, OSError, TypeError, AttributeError) as exc:
        if getattr(args, 'json', False) or getattr(args, 'format', None) == 'json':
            _output({'error': str(exc), 'runtime_verified': False})
        else:
            Console(stderr=True).print(f'Error: {exc}', markup=False)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
