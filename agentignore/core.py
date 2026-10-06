"""Core audit engine and path matching logic for agentignore."""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import pathspec

from agentignore.constants import (
    SUPPORTED_TARGETS,
    TARGET_FILENAME_MAP,
)
from agentignore.detector import (
    detect_project_stacks,
    is_bloat_path,
    is_lockfile_path,
    is_sensitive_path,
)


class IgnoreRuleSet:
    """Represents a set of ignore patterns with standard gitignore logic."""

    def __init__(self, patterns: Optional[List[str]] = None, source: Optional[str] = None):
        self.source = source or "in-memory"
        self.raw_lines = patterns or []
        # Filter comments and empty lines for the spec
        clean_patterns = [
            line.strip()
            for line in self.raw_lines
            if line.strip() and not line.strip().startswith("#")
        ]
        self.spec = pathspec.PathSpec.from_lines("gitignore", clean_patterns)

    @classmethod
    def from_file(cls, filepath: Path) -> "IgnoreRuleSet":
        if not filepath.exists() or not filepath.is_file():
            return cls([], source=str(filepath))
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = [line.rstrip("\r\n") for line in f]
            return cls(lines, source=str(filepath))
        except Exception:
            return cls([], source=str(filepath))

    def matches(self, rel_path: str) -> bool:
        normalized = rel_path.replace("\\", "/").lstrip("/")
        return bool(self.spec.match_file(normalized))


@dataclass
class Leak:
    """Represents an unshielded file or directory that is exposed to AI tools."""

    path: str
    category: str  # "sensitive", "git_ignored", "bloat", "lockfile"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    description: str
    unshielded_targets: List[str]  # e.g. [".cursorignore", ".claudeignore"]
    size_bytes: int = 0
    estimated_tokens: int = 0


@dataclass
class AuditReport:
    """Result of an agentignore audit run."""

    repo_path: Path
    detected_stacks: List[str]
    existing_configs: Dict[str, bool]
    scanned_files_count: int
    leaks: List[Leak] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.leaks) == 0

    @property
    def critical_leaks_count(self) -> int:
        return sum(1 for leak in self.leaks if leak.severity == "CRITICAL")

    @property
    def total_wasted_tokens(self) -> int:
        return sum(leak.estimated_tokens for leak in self.leaks)


def get_dir_size(dir_path: Path) -> int:
    """Recursively calculate the total size of a directory in bytes."""
    total = 0
    try:
        for entry in os.scandir(dir_path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_dir_size(Path(entry.path))
            except OSError:
                pass
    except OSError:
        pass
    return total


def audit_repository(
    repo_path: Path,
    target_names: Optional[List[str]] = None,
    check_lockfiles: bool = True,
) -> AuditReport:
    """Audit a repository for files and directories exposed to AI coding tools."""
    if target_names is None:
        target_names = ["cursor", "claude", "cline", "copilot", "windsurf"]

    target_files = {name: TARGET_FILENAME_MAP[name] for name in target_names if name in TARGET_FILENAME_MAP}

    # Detect active configs in the repository
    existing_configs: Dict[str, bool] = {}
    rule_sets: Dict[str, IgnoreRuleSet] = {}

    for name, filename in target_files.items():
        file_path = repo_path / filename
        exists = file_path.exists()
        existing_configs[filename] = exists
        rule_sets[filename] = IgnoreRuleSet.from_file(file_path)

    # Check universal .agentignore as well
    universal_path = repo_path / ".agentignore"
    existing_configs[".agentignore"] = universal_path.exists()
    universal_rules = IgnoreRuleSet.from_file(universal_path)

    # Load .gitignore
    gitignore_path = repo_path / ".gitignore"
    git_rules = IgnoreRuleSet.from_file(gitignore_path)

    stacks = detect_project_stacks(repo_path)
    leaks: List[Leak] = []
    scanned_count = 0

    skip_vcs = {".git", ".svn", ".hg"}

    # Walk directory tree with smart pruning for bloat directories
    for root, dirs, files in os.walk(repo_path, topdown=True):
        # 1. Prune VCS directories
        dirs[:] = [d for d in dirs if d not in skip_vcs]

        root_path = Path(root)
        try:
            rel_root = root_path.relative_to(repo_path).as_posix()
            if rel_root == ".":
                rel_root = ""
        except ValueError:
            continue

        # 2. Check directories for whole-directory bloat or git-ignored status
        dirs_to_prune = []
        for d in dirs:
            dir_rel = f"{rel_root}/{d}" if rel_root else d
            dir_slash = f"{dir_rel}/"

            is_dir_bloat = is_bloat_path(dir_slash)
            is_dir_git_ignored = git_rules.matches(dir_slash)

            if is_dir_bloat or is_dir_git_ignored:
                # Check if all AI targets properly shield this directory
                unshielded: List[str] = []
                for filename, ruleset in rule_sets.items():
                    has_own = ruleset.matches(dir_slash)
                    has_uni = universal_rules.matches(dir_slash)
                    if not has_own and not has_uni:
                        unshielded.append(filename)

                # Always prune this directory from descending into its thousands of files
                dirs_to_prune.append(d)

                if unshielded:
                    dir_full_path = root_path / d
                    dir_size = get_dir_size(dir_full_path)
                    est_tokens = max(1, dir_size // 4)
                    category = "bloat" if is_dir_bloat else "git_ignored"
                    description = f"Unshielded directory (~{dir_size // 1024:,} KB)"

                    leaks.append(
                        Leak(
                            path=dir_slash,
                            category=category,
                            severity="HIGH" if dir_size > 100000 else "MEDIUM",
                            description=description,
                            unshielded_targets=unshielded,
                            size_bytes=dir_size,
                            estimated_tokens=est_tokens,
                        )
                    )

        # Apply directory pruning
        for d in dirs_to_prune:
            dirs.remove(d)

        # 3. Check remaining files
        for f in files:
            scanned_count += 1
            if f in existing_configs:
                continue

            file_rel = f"{rel_root}/{f}" if rel_root else f
            file_full = root_path / f

            size_bytes = 0
            try:
                size_bytes = file_full.stat().st_size
            except OSError:
                pass

            estimated_tokens = max(1, size_bytes // 4)

            category: Optional[str] = None
            severity: str = "LOW"
            description: str = ""

            if is_sensitive_path(file_rel):
                category = "sensitive"
                severity = "CRITICAL"
                description = "Secret/credential file exposed to AI context"
            elif git_rules.matches(file_rel):
                category = "git_ignored"
                severity = "HIGH" if size_bytes > 50000 else "MEDIUM"
                description = f"Git-ignored file exposed ({size_bytes // 1024} KB)"
            elif is_bloat_path(file_rel):
                category = "bloat"
                severity = "MEDIUM"
                description = f"Context bloat file ({size_bytes // 1024} KB)"
            elif check_lockfiles and is_lockfile_path(file_rel):
                category = "lockfile"
                severity = "MEDIUM"
                description = f"Heavy lockfile ({estimated_tokens:,} tokens)"

            if category is None:
                continue

            unshielded = []
            for filename, ruleset in rule_sets.items():
                has_own = ruleset.matches(file_rel)
                has_uni = universal_rules.matches(file_rel)
                if not has_own and not has_uni:
                    unshielded.append(filename)

            if unshielded:
                leaks.append(
                    Leak(
                        path=file_rel,
                        category=category,
                        severity=severity,
                        description=description,
                        unshielded_targets=unshielded,
                        size_bytes=size_bytes,
                        estimated_tokens=estimated_tokens,
                    )
                )

    return AuditReport(
        repo_path=repo_path,
        detected_stacks=stacks,
        existing_configs=existing_configs,
        scanned_files_count=scanned_count,
        leaks=leaks,
    )
