"""Stack detector and pattern matchers for agentignore."""

from pathlib import Path
from typing import Dict, List, Set
import pathspec

from agentignore.constants import (
    DEFAULT_BLOAT_PATTERNS,
    LOCKFILE_PATTERNS,
    SENSITIVE_PATTERNS,
)

STACK_SIGNATURES: Dict[str, List[str]] = {
    "Node.js / TypeScript": [
        "package.json",
        "tsconfig.json",
        "pnpm-workspace.yaml",
        "bun.lockb",
    ],
    "Python": [
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "Pipfile",
        "environment.yml",
    ],
    "Rust": ["Cargo.toml"],
    "Go": ["go.mod", "go.sum"],
    "Java / Kotlin": ["pom.xml", "build.gradle", "build.gradle.kts"],
    "PHP": ["composer.json"],
    "Ruby": ["Gemfile"],
    ".NET / C#": ["*.csproj", "*.sln"],
    "Docker": ["Dockerfile", "docker-compose.yml", "compose.yaml"],
}

STACK_SPECIFIC_PATTERNS: Dict[str, List[str]] = {
    "Node.js / TypeScript": [
        "node_modules/",
        ".npm/",
        ".yarn/",
        ".pnpm-store/",
        ".next/",
        ".nuxt/",
        "dist/",
        "build/",
    ],
    "Python": [
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        ".venv/",
        "venv/",
        "*.egg-info/",
    ],
    "Rust": [
        "target/",
        "**/*.rs.bk",
    ],
    "Go": [
        "bin/",
        "pkg/",
    ],
    "Java / Kotlin": [
        "target/",
        ".gradle/",
        "build/",
        "*.class",
        "*.jar",
        "*.war",
    ],
    "PHP": [
        "vendor/",
    ],
    "Ruby": [
        "vendor/bundle/",
    ],
    ".NET / C#": [
        "bin/",
        "obj/",
    ],
    "Docker": [],
}


def detect_project_stacks(repo_path: Path) -> List[str]:
    """Detect the technology stacks present in the given repository path."""
    detected: List[str] = []
    if not repo_path.exists() or not repo_path.is_dir():
        return detected

    for stack, signatures in STACK_SIGNATURES.items():
        found = False
        for sig in signatures:
            if "*" in sig:
                if any(repo_path.glob(sig)):
                    found = True
                    break
            else:
                if (repo_path / sig).exists():
                    found = True
                    break
        if found:
            detected.append(stack)

    return detected


def get_stack_patterns(stacks: List[str]) -> List[str]:
    """Get recommended ignore patterns for the detected stacks."""
    patterns: Set[str] = set()
    for stack in stacks:
        for pat in STACK_SPECIFIC_PATTERNS.get(stack, []):
            patterns.add(pat)
    return sorted(list(patterns))


# Pre-compiled pathspecs for fast pattern checks
_SENSITIVE_SPEC = pathspec.PathSpec.from_lines("gitignore", SENSITIVE_PATTERNS)
_BLOAT_SPEC = pathspec.PathSpec.from_lines("gitignore", DEFAULT_BLOAT_PATTERNS)
_LOCKFILE_SPEC = pathspec.PathSpec.from_lines("gitignore", LOCKFILE_PATTERNS)


def is_sensitive_path(rel_path: str) -> bool:
    """Return True if the relative file path matches known sensitive patterns."""
    normalized = rel_path.replace("\\", "/")
    # Check both the full path and the basename
    basename = Path(normalized).name
    return _SENSITIVE_SPEC.match_file(normalized) or _SENSITIVE_SPEC.match_file(basename)


def is_bloat_path(rel_path: str) -> bool:
    """Return True if the relative file path matches known bloat patterns."""
    normalized = rel_path.replace("\\", "/")
    basename = Path(normalized).name
    return _BLOAT_SPEC.match_file(normalized) or _BLOAT_SPEC.match_file(basename)


def is_lockfile_path(rel_path: str) -> bool:
    """Return True if the relative path is a package manager lockfile."""
    normalized = rel_path.replace("\\", "/")
    basename = Path(normalized).name
    return _LOCKFILE_SPEC.match_file(normalized) or _LOCKFILE_SPEC.match_file(basename)
