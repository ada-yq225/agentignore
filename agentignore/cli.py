"""Command line interface for agentignore with rich terminal output."""

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
from agentignore.constants import SUPPORTED_TARGETS
from agentignore.core import audit_repository
from agentignore.syncer import sync_repository

console = Console()
err_console = Console(stderr=True)


def print_banner():
    banner = Text()
    banner.append("🛡️  agentignore ", style="bold cyan")
    banner.append(f"v{__version__}", style="dim")
    banner.append(" — Universal AI Context Shield & Ignore Compiler", style="bold white")
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
    )

    if args.json:
        data = {
            "version": __version__,
            "repo_path": str(report.repo_path),
            "is_clean": report.is_clean,
            "detected_stacks": report.detected_stacks,
            "scanned_files_count": report.scanned_files_count,
            "critical_leaks_count": report.critical_leaks_count,
            "total_wasted_tokens": report.total_wasted_tokens,
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

    # Tech stack info
    stacks_str = ", ".join(report.detected_stacks) if report.detected_stacks else "Generic"
    console.print(f"[dim]Project Stacks:[/dim] [bold]{stacks_str}[/bold]  [dim]Files Scanned:[/dim] {report.scanned_files_count}")

    # Configs presence summary
    config_tags = []
    for filename, exists in report.existing_configs.items():
        if exists:
            config_tags.append(f"[green]✓ {filename}[/green]")
        else:
            config_tags.append(f"[dim]✗ {filename}[/dim]")
    console.print(f"[dim]Active Shields:[/dim] {' '.join(config_tags)}")
    console.print()

    if report.is_clean:
        panel_content = Text()
        panel_content.append("✓ ALL CLEAN & SECURE!\n", style="bold green")
        panel_content.append(
            "No credentials, private keys, or context bloat are exposed to your AI coding tools.\n",
            style="white",
        )
        panel_content.append("Your repository context is optimized for token efficiency.", style="dim")
        console.print(Panel(panel_content, border_style="green", padding=(1, 2)))
        return 0

    # There are leaks! Print the leak table
    table = Table(
        title=f"⚠️  Context Leaks Detected ({len(report.leaks)} items exposed to AI)",
        title_style="bold red",
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("Severity", style="bold", width=10, justify="center")
    table.add_column("File Path", style="cyan", no_wrap=False)
    table.add_column("Category", style="yellow", width=14)
    table.add_column("Exposed To", style="magenta")
    table.add_column("Tokens (Est.)", style="green", justify="right", width=14)

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

        table.add_row(
            Text(leak.severity, style=sev_style),
            leak.path,
            leak.category,
            exposed_str,
            tokens_str,
        )

    console.print(table)
    console.print()

    # Warning summary panel
    crit_count = report.critical_leaks_count
    tokens_count = report.total_wasted_tokens

    summary_lines = []
    if crit_count > 0:
        summary_lines.append(f"[bold red]🚨 CRITICAL RISK:[/bold red] {crit_count} secret/credential files exposed to AI tools!")
    if tokens_count > 0:
        summary_lines.append(f"[yellow]⚡ Token Waste:[/yellow] ~{tokens_count:,} unnecessary tokens being read per query.")

    summary_lines.append("\n[bold cyan]👉 Recommendation:[/bold cyan] Run [bold white]`agentignore sync`[/bold white] to auto-shield these files across all AI tools.")

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

    action_label = "Dry-run sync" if args.dry_run else "Syncing AI Ignore Files"
    table = Table(title=f"🔄 {action_label}", title_style="bold cyan", header_style="bold magenta")
    table.add_column("Target File", style="white")
    table.add_column("Status", justify="center")

    status_styles = {
        "created": "[bold green]Created[/bold green]",
        "updated": "[bold yellow]Updated[/bold yellow]",
        "unchanged": "[dim]Unchanged (Up-to-date)[/dim]",
    }

    for filename, status in results.items():
        table.add_row(filename, status_styles.get(status, status))

    console.print(table)
    console.print()

    if not args.dry_run:
        console.print("[bold green]✓ Sync completed successfully![/bold green] All AI tools are now synchronized.")
        console.print("[dim]Verifying with a quick audit...[/dim]")
        console.print()
        # Verify immediately
        verify_report = audit_repository(repo_path, target_names=targets)
        if verify_report.is_clean:
            console.print("[bold green]🎉 Perfect! 0 leaks remaining.[/bold green] Your repository is now fully shielded.")
        else:
            console.print(f"[yellow]Notice: {len(verify_report.leaks)} files still flagged. Run `agentignore check` for details.[/yellow]")

    return 0


def handle_targets(args: argparse.Namespace) -> int:
    print_banner()
    console.print()

    repo_path = Path(args.path).resolve()
    table = Table(title="Supported AI Tools & Target Files", title_style="bold cyan")
    table.add_column("Target Key", style="cyan")
    table.add_column("Tool Name", style="white")
    table.add_column("Ignore File", style="green")
    table.add_column("Configured Locally?", justify="center")
    table.add_column("Description", style="dim")

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

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: check / audit
    check_parser = subparsers.add_parser("check", aliases=["audit"], help="Audit repository for files exposed to AI tools")
    check_parser.add_argument("--path", "-p", default=".", help="Target repository directory (default: current)")
    check_parser.add_argument("--targets", "-t", help="Comma-separated target keys (e.g. cursor,claude)")
    check_parser.add_argument("--strict", action="store_true", default=True, help="Exit with code 1 if leaks are found (default: True)")
    check_parser.add_argument("--no-strict", dest="strict", action="store_false", help="Always exit with code 0 even if leaks are found")
    check_parser.add_argument("--ignore-lockfiles", action="store_true", help="Do not flag package lockfiles as leaks")
    check_parser.add_argument("--json", action="store_true", help="Output audit report as structured JSON")

    # Command: sync
    sync_parser = subparsers.add_parser("sync", help="Synchronize unified ignore rules to all AI tools")
    sync_parser.add_argument("--path", "-p", default=".", help="Target repository directory (default: current)")
    sync_parser.add_argument("--targets", "-t", help="Comma-separated target keys to sync")
    sync_parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    sync_parser.add_argument("--include-lockfiles", action="store_true", help="Include lockfiles in the generated ignore lists")

    # Command: init
    init_parser = subparsers.add_parser("init", help="Initialize .agentignore and sync across all AI tools")
    init_parser.add_argument("--path", "-p", default=".", help="Target repository directory (default: current)")

    # Command: targets
    targets_parser = subparsers.add_parser("targets", help="List all supported AI tools and local statuses")
    targets_parser.add_argument("--path", "-p", default=".", help="Target repository directory (default: current)")

    args = parser.parse_args(argv)

    if not args.command:
        # Default behavior when running with no arguments: run check
        args.command = "check"
        args.path = "."
        args.targets = None
        args.strict = False
        args.ignore_lockfiles = False
        args.json = False
        return handle_check(args)

    if args.command in ("check", "audit"):
        return handle_check(args)
    elif args.command == "sync":
        return handle_sync(args)
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
