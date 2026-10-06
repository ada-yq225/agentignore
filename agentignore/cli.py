"""Codex / Claude policy compiler and honest static audit CLI."""
import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from agentignore import __version__
from agentignore.adapters import LIMITATIONS
from agentignore.constants import SUPPORTED_TARGETS
from agentignore.core import audit_repository
from agentignore.cost import estimate_dollar_cost
from agentignore.exporter import export_json_report, export_markdown_report
from agentignore.hooks import install_pre_commit_hook, uninstall_pre_commit_hook
from agentignore.i18n import detect_system_language
from agentignore.syncer import compute_ignore_diff, sync_repository, validate_targets

console = Console()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog='agentignore', description='Project-local deny policy compiler for Codex and Claude Code')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--lang', choices=['en', 'zh'], default=None)
    commands = parser.add_subparsers(dest='command')
    for command in ('check', 'audit', 'sync', 'init', 'diff', 'targets', 'cost', 'hook'):
        sub = commands.add_parser(command)
        sub.add_argument('--path', '-p', default='.')
        if command in ('check', 'audit', 'sync', 'init'):
            sub.add_argument('--targets', '-t', help='codex,claude (default: both)')
        if command in ('check', 'audit'):
            sub.add_argument('--strict', action='store_true', default=True)
            sub.add_argument('--no-strict', dest='strict', action='store_false')
            sub.add_argument('--json', action='store_true')
            sub.add_argument('--export')
            sub.add_argument('--deep', action='store_true')
            sub.add_argument('--ignore-lockfiles', action='store_true')
        if command in ('sync', 'init'):
            sub.add_argument('--dry-run', action='store_true')
            sub.add_argument('--include-lockfiles', action='store_true', help='Deny lockfile reads too; may interfere with dependency work')
        if command == 'diff':
            sub.add_argument('--target', choices=list(SUPPORTED_TARGETS), default='codex')
        if command == 'cost':
            sub.add_argument('--queries', type=int, default=100)
            sub.add_argument('--input-rate', type=float, required=True, help='Your input price in USD per million tokens')
        if command == 'hook':
            sub.add_argument('action', choices=['install', 'uninstall'])
    args = parser.parse_args(argv)
    if args.command is None:
        return main(['--lang', args.lang or detect_system_language(), 'check'])
    zh = (args.lang or detect_system_language()) == 'zh'
    repo = Path(args.path).resolve()
    try:
        if not repo.is_dir():
            raise ValueError(f'Not a directory: {repo}')
        targets = validate_targets([x.strip() for x in args.targets.split(',')] if getattr(args, 'targets', None) else None)
        if args.command in ('check', 'audit'):
            report = audit_repository(repo, targets, not args.ignore_lockfiles, args.deep)
            data = dict(version=__version__, **report.to_dict())
            if args.export:
                output = Path(args.export)
                (export_json_report if output.suffix == '.json' else export_markdown_report)(data, output)
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                console.print('静态配置检查（未验证运行时限制）' if zh else 'Static configuration check (runtime enforcement not verified)')
                for error in report.configuration_errors:
                    console.print(error, style='red', markup=False)
                table = Table('Severity', 'Path', 'Category', 'Missing deny config', 'Potential tokens')
                for finding in report.leaks:
                    table.add_row(finding.severity, finding.path, finding.category, ', '.join(finding.unshielded_targets), str(finding.estimated_tokens))
                console.print(table)
                console.print('未发现静态问题；不代表零泄漏。' if zh and report.is_clean else
                              'No static findings; this is not a security guarantee.' if report.is_clean else
                              '发现配置或文件风险，请查看报告。' if zh else 'Configuration or file-risk findings detected.')
                for limitation in LIMITATIONS:
                    console.print(limitation, style='dim', markup=False)
            return 1 if args.strict and not report.is_clean else 0
        if args.command in ('sync', 'init'):
            result = sync_repository(repo, targets, args.dry_run, args.include_lockfiles)
            for path, status in result.items():
                console.print(f'{path}: {status}' + (' (dry run)' if args.dry_run else ''), markup=False)
            console.print('配置已生成，请重启客户端并验证实际权限。' if zh else 'Review settings, restart the client, and verify effective permissions.')
            console.print('Codex: inherited sandbox_mode settings override permission profiles. Project config requires trust.')
            return 0
        if args.command == 'diff':
            console.print(json.dumps(compute_ignore_diff(repo, args.target), indent=2), markup=False)
            return 0
        if args.command == 'targets':
            for key, info in SUPPORTED_TARGETS.items():
                console.print(f'{key}: {info["filename"]} — {info["description"]}', markup=False)
            return 0
        if args.command == 'cost':
            if args.queries < 1 or args.input_rate < 0:
                raise ValueError('queries must be positive and input-rate nonnegative')
            tokens = audit_repository(repo).potential_context_tokens
            value = estimate_dollar_cost(tokens, args.queries, input_rate=args.input_rate)
            console.print(f'Hypothetical full-read scenario: ~{tokens:,} potential tokens × {args.queries} reads = ${value:.2f}.')
            console.print('Not measured savings. Assumes every flagged text file is read in full on every request, without caching.')
            return 0
        if args.command == 'hook':
            ok, message = (install_pre_commit_hook if args.action == 'install' else uninstall_pre_commit_hook)(repo)
            console.print(message, markup=False)
            return 0 if ok else 1
    except (ValueError, OSError, TypeError, AttributeError) as exc:
        if getattr(args, 'json', False):
            print(json.dumps({'error': str(exc), 'runtime_verified': False}))
        else:
            Console(stderr=True).print(f'Error: {exc}', markup=False)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
