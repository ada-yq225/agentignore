"""Command line interface for agentignore with rich bilingual terminal output."""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from agentignore import __version__
from agentignore.constants import SUPPORTED_TARGETS, TARGET_FILENAME_MAP
from agentignore.core import audit_repository
from agentignore.cost import estimate_dollar_cost, get_all_model_costs
from agentignore.exporter import export_json_report, export_markdown_report
from agentignore.hooks import install_pre_commit_hook, uninstall_pre_commit_hook
from agentignore.i18n import detect_system_language, set_language, t
from agentignore.syncer import compute_ignore_diff, sync_repository

console = Console()
err_console = Console(stderr=True)


def print_banner():
    banner = Text()
    banner.append("🛡️  agentignore ", style="bold cyan")
    banner.append(f"v{__version__}", style="dim")
    banner.append(f" — {t('banner_tag')}", style="bold white")
    console.print(banner)


def handle_check(args: argparse.Namespace) -> int:
    repo_path = Path(args.path).resolve()
    if not repo_path.exists() or not repo_path.is_dir():
        err_console.print(f"[red]Error:[/red] Path '{repo_path}' is not a valid directory.")
        return 2

    targets = args.targets.split(",") if args.targets else None
    report = audit_repository(
        repo_path,
        target_names=targets,
        check_lockfiles=not args.ignore_lockfiles,
        deep_scan=getattr(args, "deep", False),
    )

    # Export report if requested
    if getattr(args, "export", None):
        export_path = Path(args.export)
        report_dict = {
            "version": __version__,
            "repo_path": str(report.repo_path),
            "is_clean": report.is_clean,
            "detected_stacks": report.detected_stacks,
            "scanned_files_count": report.scanned_files_count,
            "critical_leaks_count": report.critical_leaks_count,
            "total_wasted_tokens": report.total_wasted_tokens,
            "total_wasted_cost_100_queries": report.total_wasted_cost_100_queries,
            "leaks": [
                {
                    "path": leak.path,
                    "category": leak.category,
                    "severity": leak.severity,
                    "description": leak.description,
                    "unshielded_targets": leak.unshielded_targets,
                    "estimated_tokens": leak.estimated_tokens,
                }
                for leak in report.leaks
            ],
        }
        if export_path.suffix.lower() == ".json":
            export_json_report(report_dict, export_path)
        else:
            export_markdown_report(report_dict, export_path)
        console.print(f"[green]✓ Exported audit report to:[/green] [bold]{export_path}[/bold]")

    if args.json:
        data = {
            "version": __version__,
            "repo_path": str(report.repo_path),
            "is_clean": report.is_clean,
            "detected_stacks": report.detected_stacks,
            "scanned_files_count": report.scanned_files_count,
            "critical_leaks_count": report.critical_leaks_count,
            "total_wasted_tokens": report.total_wasted_tokens,
            "total_wasted_cost_100_queries": report.total_wasted_cost_100_queries,
            "leaks": [
                {
                    "path": leak.path,
                    "category": leak.category,
                    "severity": leak.severity,
                    "description": leak.description,
                    "unshielded_targets": leak.unshielded_targets,
                    "estimated_tokens": leak.estimated_tokens,
                }
                for leak in report.leaks
            ],
        }
        print(json.dumps(data, indent=2))
        return 1 if (not report.is_clean and args.strict) else 0

    print_banner()
    console.print()

    if getattr(args, "deep", False):
        console.print(f"[cyan]{t('deep_scan_banner')}[/cyan]")

    # Tech stack info
    stacks_str = ", ".join(report.detected_stacks) if report.detected_stacks else "Generic"
    console.print(f"[dim]{t('project_stacks')}:[/dim] [bold]{stacks_str}[/bold]  [dim]{t('files_scanned')}:[/dim] {report.scanned_files_count}")

    # Configs presence summary
    config_tags = []
    for filename, exists in report.existing_configs.items():
        if exists:
            config_tags.append(f"[green]✓ {filename}[/green]")
        else:
            config_tags.append(f"[dim]✗ {filename}[/dim]")
    console.print(f"[dim]{t('active_shields')}:[/dim] {' '.join(config_tags)}")
    console.print()

    if report.is_clean:
        panel_content = Text()
        panel_content.append(f"{t('all_clean_title')}\n", style="bold green")
        panel_content.append(f"{t('all_clean_msg1')}\n", style="white")
        panel_content.append(t('all_clean_msg2'), style="dim")
        console.print(Panel(panel_content, border_style="green", padding=(1, 2)))
        return 0

    # There are leaks! Print the leak table
    table = Table(
        title=t("leaks_detected_title", count=len(report.leaks)),
        title_style="bold red",
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column(t("col_severity"), style="bold", width=10, justify="center")
    table.add_column(t("col_path"), style="cyan", no_wrap=False)
    table.add_column(t("col_category"), style="yellow", width=14)
    table.add_column(t("col_exposed_to"), style="magenta")
    table.add_column(t("col_tokens"), style="green", justify="right", width=14)
    if getattr(args, "cost", False):
        table.add_column(t("col_cost"), style="yellow", justify="right", width=14)

    severity_colors = {
        "CRITICAL": "bold red",
        "HIGH": "bold yellow",
        "MEDIUM": "cyan",
        "LOW": "dim",
    }

    for leak in report.leaks:
        sev_style = severity_colors.get(leak.severity, "white")
        exposed_str = ", ".join(leak.unshielded_targets)
        tokens_str = f"~{leak.estimated_tokens:,}" if leak.estimated_tokens > 0 else "-"

        row_items = [
            Text(leak.severity, style=sev_style),
            leak.path,
            leak.category,
            exposed_str,
            tokens_str,
        ]
        if getattr(args, "cost", False):
            row_items.append(f"${leak.estimated_cost_100_queries:.2f}")

        table.add_row(*row_items)

    console.print(table)
    console.print()

    # Warning summary panel
    crit_count = report.critical_leaks_count
    tokens_count = report.total_wasted_tokens
    cost_amount = report.total_wasted_cost_100_queries

    summary_lines = []
    if crit_count > 0:
        summary_lines.append(f"[bold red]{t('critical_risk_title')}:[/bold red] {t('critical_risk_msg', count=crit_count)}")
    if tokens_count > 0:
        summary_lines.append(f"[yellow]{t('token_waste_title')}:[/yellow] {t('token_waste_msg', tokens=tokens_count, cost=cost_amount)}")

    summary_lines.append(f"\n[bold cyan]{t('recommendation')}[/bold cyan]")

    console.print(Panel("\n".join(summary_lines), border_style="red" if crit_count > 0 else "yellow", padding=(1, 2)))

    return 1 if args.strict else 0


def handle_sync(args: argparse.Namespace) -> int:
    repo_path = Path(args.path).resolve()
    if not repo_path.exists() or not repo_path.is_dir():
        err_console.print(f"[red]Error:[/red] Path '{repo_path}' is not a valid directory.")
        return 2

    print_banner()
    console.print()

    targets = args.targets.split(",") if args.targets else None
    results = sync_repository(
        repo_path=repo_path,
        targets=targets,
        dry_run=args.dry_run,
        include_lockfiles=args.include_lockfiles,
    )

    action_label = t("sync_dry_title") if args.dry_run else t("sync_title")
    table = Table(title=action_label, title_style="bold cyan", header_style="bold magenta")
    table.add_column(t("col_target_file"), style="white")
    table.add_column(t("col_status"), justify="center")

    status_labels = {
        "created": f"[bold green]{t('status_created')}[/bold green]",
        "updated": f"[bold yellow]{t('status_updated')}[/bold yellow]",
        "unchanged": f"[dim]{t('status_unchanged')}[/dim]",
    }

    for filename, status in results.items():
        table.add_row(filename, status_labels.get(status, status))

    console.print(table)
    console.print()

    if not args.dry_run:
        console.print(f"[bold green]{t('sync_success', count=len(results))}[/bold green]")
        console.print(f"[dim]{t('quick_audit')}[/dim]\n")
        verify_report = audit_repository(repo_path, target_names=targets)
        if verify_report.is_clean:
            console.print(f"[bold green]{t('perfect_shield')}[/bold green]")
        else:
            console.print(f"[yellow]{t('notice_remaining', count=len(verify_report.leaks))}[/yellow]")

    return 0


def handle_diff(args: argparse.Namespace) -> int:
    repo_path = Path(args.path).resolve()
    print_banner()
    console.print()

    target = getattr(args, "target", "cursor")
    diff_data = compute_ignore_diff(repo_path, target_key=target)

    table = Table(title=f"{t('diff_title')} ({target})", title_style="bold cyan")
    table.add_column("Type", style="bold", width=22)
    table.add_column("Pattern", style="white")

    for pat in diff_data["missing_in_ai"]:
        table.add_row("[red]Missing in AI Shield[/red]", pat)
    for pat in diff_data["unique_in_ai"]:
        table.add_row("[green]Unique in AI Shield[/green]", pat)

    if not diff_data["missing_in_ai"] and not diff_data["unique_in_ai"]:
        console.print("[green]✓ .gitignore and AI ignore rules are in identical alignment.[/green]")
    else:
        console.print(table)

    return 0


def handle_cost(args: argparse.Namespace) -> int:
    print_banner()
    console.print()

    repo_path = Path(args.path).resolve()
    report = audit_repository(repo_path)
    tokens = report.total_wasted_tokens
    queries = getattr(args, "queries", 100)

    table = Table(title=f"{t('cost_report_title')} ({queries} Queries, ~{tokens:,} Tokens/Q)", title_style="bold yellow")
    table.add_column("Model Name", style="cyan")
    table.add_column("Provider", style="dim")
    table.add_column("Cost Rate / 1M Tokens", justify="right")
    table.add_column(f"Wasted Dollar Cost ({queries} Qs)", style="bold red", justify="right")

    costs = get_all_model_costs(tokens, queries=queries)
    from agentignore.cost import MODEL_PRICING

    for model, total_cost in costs.items():
        rate = MODEL_PRICING[model]["rate"]
        provider = MODEL_PRICING[model]["provider"]
        table.add_row(
            model,
            provider,
            f"${rate:.2f}",
            f"${total_cost:.2f}",
        )

    console.print(table)
    return 0


def handle_hook(args: argparse.Namespace) -> int:
    repo_path = Path(args.path).resolve()
    action = getattr(args, "action", "install")

    if action == "install":
        ok, msg = install_pre_commit_hook(repo_path)
        if ok:
            console.print(f"[bold green]{t('hook_installed', path=msg)}[/bold green]")
            return 0
        else:
            err_console.print(f"[red]Error installing hook:[/red] {msg}")
            return 1
    elif action == "uninstall":
        ok, msg = uninstall_pre_commit_hook(repo_path)
        if ok:
            console.print(f"[bold green]{t('hook_uninstalled', path=msg)}[/bold green]")
            return 0
        else:
            err_console.print(f"[yellow]Notice:[/yellow] {msg}")
            return 1
    return 0


def handle_targets(args: argparse.Namespace) -> int:
    print_banner()
    console.print()

    repo_path = Path(args.path).resolve()
    table = Table(title=t("targets_title", count=len(SUPPORTED_TARGETS)), title_style="bold cyan")
    table.add_column(t("col_target_key"), style="cyan")
    table.add_column(t("col_tool_name"), style="white")
    table.add_column(t("col_ignore_file"), style="green")
    table.add_column(t("col_configured"), justify="center")
    table.add_column(t("col_description"), style="dim")

    for key, info in SUPPORTED_TARGETS.items():
        filename = info["filename"]
        exists = (repo_path / filename).exists()
        configured = "[bold green]YES[/bold green]" if exists else "[dim]NO[/dim]"
        table.add_row(
            key,
            info["name"],
            filename,
            configured,
            info["description"],
        )

    console.print(table)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agentignore",
        description="The Universal AI Context Shield & Ignore Compiler for Cursor, Claude Code, Cline, Copilot, and Windsurf.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--lang", choices=["en", "zh"], default=None, help="Set UI language (en or zh)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: check / audit
    check_parser = subparsers.add_parser("check", aliases=["audit"], help="Audit repository for files exposed to AI tools")
    check_parser.add_argument("--path", "-p", default=".", help="Target repository directory")
    check_parser.add_argument("--targets", "-t", help="Comma-separated target keys")
    check_parser.add_argument("--strict", action="store_true", default=True, help="Exit with code 1 if leaks are found")
    check_parser.add_argument("--no-strict", dest="strict", action="store_false", help="Exit with code 0 even if leaks are found")
    check_parser.add_argument("--ignore-lockfiles", action="store_true", help="Do not flag package lockfiles as leaks")
    check_parser.add_argument("--deep", "-d", action="store_true", help="Scan file content for leaked API keys & secrets")
    check_parser.add_argument("--cost", "-c", action="store_true", help="Display estimated dollar cost per 100 queries")
    check_parser.add_argument("--export", "-e", help="Export report to Markdown (.md) or JSON (.json)")
    check_parser.add_argument("--json", action="store_true", help="Output audit report as structured JSON")

    # Command: sync
    sync_parser = subparsers.add_parser("sync", help="Synchronize unified ignore rules to all AI tools")
    sync_parser.add_argument("--path", "-p", default=".", help="Target repository directory")
    sync_parser.add_argument("--targets", "-t", help="Comma-separated target keys to sync")
    sync_parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    sync_parser.add_argument("--include-lockfiles", action="store_true", help="Include lockfiles in the generated ignore lists")

    # Command: diff
    diff_parser = subparsers.add_parser("diff", help="Compare rules between .gitignore and AI ignore files")
    diff_parser.add_argument("--path", "-p", default=".", help="Target repository directory")
    diff_parser.add_argument("--target", "-t", default="cursor", help="Target AI tool to compare against")

    # Command: cost
    cost_parser = subparsers.add_parser("cost", help="Calculate dollar cost waste across major LLM providers")
    cost_parser.add_argument("--path", "-p", default=".", help="Target repository directory")
    cost_parser.add_argument("--queries", "-q", type=int, default=100, help="Number of queries to benchmark (default: 100)")

    # Command: hook
    hook_parser = subparsers.add_parser("hook", help="Manage Git pre-commit hooks")
    hook_parser.add_argument("action", choices=["install", "uninstall"], help="Install or uninstall hook")
    hook_parser.add_argument("--path", "-p", default=".", help="Target repository directory")

    # Command: init
    init_parser = subparsers.add_parser("init", help="Initialize .agentignore and sync across all AI tools")
    init_parser.add_argument("--path", "-p", default=".", help="Target repository directory")

    # Command: targets
    targets_parser = subparsers.add_parser("targets", help="List all supported AI tools and local statuses")
    targets_parser.add_argument("--path", "-p", default=".", help="Target repository directory")

    args = parser.parse_args(argv)

    # Set language
    if args.lang:
        set_language(args.lang)
    else:
        set_language(detect_system_language())

    if not args.command:
        args.command = "check"
        args.path = "."
        args.targets = None
        args.strict = False
        args.ignore_lockfiles = False
        args.deep = False
        args.cost = False
        args.export = None
        args.json = False
        return handle_check(args)

    if args.command in ("check", "audit"):
        return handle_check(args)
    elif args.command == "sync":
        return handle_sync(args)
    elif args.command == "diff":
        return handle_diff(args)
    elif args.command == "cost":
        return handle_cost(args)
    elif args.command == "hook":
        return handle_hook(args)
    elif args.command == "init":
        args.targets = None
        args.dry_run = False
        args.include_lockfiles = False
        return handle_sync(args)
    elif args.command == "targets":
        return handle_targets(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
