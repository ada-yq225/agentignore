"""Static configuration and file-risk audit. No runtime protection claims."""
from dataclasses import asdict, dataclass, field
import os
import hashlib
from collections import Counter
from pathlib import Path
from typing import List, Optional
import pathspec
from agentignore.adapters import LIMITATIONS, configured_patterns, covers
from agentignore.constants import TARGET_FILENAME_MAP
from agentignore.detector import detect_project_stacks, is_bloat_path, is_lockfile_path, is_sensitive_path
from agentignore.policy import read_policy
from agentignore.project import load_settings, SEVERITIES
from agentignore.scanner import is_text_file, scan_file_content
from agentignore.syncer import validate_targets


class IgnoreRuleSet:
    """Gitignore matching used for recommendations only, never permissions."""
    def __init__(self, patterns=None, source=None):
        self.source = source or 'in-memory'
        self.raw_lines = patterns or []
        self.spec = pathspec.PathSpec.from_lines('gitignore', self.raw_lines)

    @classmethod
    def from_file(cls, filepath):
        return cls(filepath.read_text(encoding='utf-8').splitlines(), str(filepath)) if filepath.exists() else cls()

    def matches(self, rel_path):
        return bool(self.spec.match_file(rel_path.replace('\\', '/').lstrip('/')))


@dataclass
class Leak:
    path: str
    category: str
    severity: str
    description: str
    unshielded_targets: List[str]
    size_bytes: int = 0
    estimated_tokens: int = 0
    line_number: Optional[int] = None
    accepted: bool = False
    acceptance_reason: Optional[str] = None
    acceptance_expires: Optional[str] = None

    @property
    def rule_id(self):
        return {'sensitive': 'AG001', 'content_secret': 'AG002', 'policy': 'AG003',
                'bloat': 'AG101', 'lockfile': 'AG102', 'git_ignored': 'AG103'}[self.category]

    @property
    def finding_id(self):
        identity = f'{self.rule_id}\0{self.path}\0{self.line_number or 0}'
        return hashlib.sha256(identity.encode('utf-8')).hexdigest()[:20]

    @property
    def remediation(self):
        if self.category == 'content_secret':
            return 'Remove the hardcoded credential and rotate it if real. Move secret values to a secret store or environment; deny rules alone do not remediate an exposed key.'
        if self.category in ('sensitive', 'policy'):
            return 'Preview agentignore sync --dry-run, resolve configuration conflicts, then sync. Restart the client and verify a fake canary.'
        return 'Review whether this file is useful to your agent. If irrelevant, add an explicit deny pattern to .agentignore.toml or .agentignore, then preview and sync.'

    def to_dict(self):
        return dict(asdict(self), id=self.finding_id, rule_id=self.rule_id, remediation=self.remediation)


@dataclass
class AuditReport:
    repo_path: Path
    detected_stacks: List[str]
    existing_configs: dict
    scanned_files_count: int
    leaks: List[Leak] = field(default_factory=list)
    configuration_errors: List[str] = field(default_factory=list)
    project: dict = field(default_factory=dict)
    fail_on: str = 'high'
    limitations: List[str] = field(default_factory=lambda: list(LIMITATIONS))

    @property
    def is_clean(self):
        """No static findings; this does not imply runtime protection."""
        return not self.leaks and not self.configuration_errors

    @property
    def critical_leaks_count(self):
        return sum(leak.severity == 'CRITICAL' for leak in self.leaks)

    @property
    def potential_context_tokens(self):
        return sum(leak.estimated_tokens for leak in self.leaks)

    def gate_failed(self, fail_on=None):
        threshold = SEVERITIES[fail_on or self.fail_on]
        return bool(self.configuration_errors) or any(
            not item.accepted and SEVERITIES[item.severity.lower()] >= threshold for item in self.leaks)

    def to_dict(self):
        counts = dict(Counter(x.severity.lower() for x in self.leaks))
        return dict(schema_version='1.0', project=self.project, fail_on=self.fail_on,
                    gate_failed=self.gate_failed(),
                    summary=dict(findings=len(self.leaks), accepted=sum(x.accepted for x in self.leaks),
                                 configuration_errors=len(self.configuration_errors), severities=counts),
                    repo_path=str(self.repo_path), is_clean=self.is_clean,
                    assessment='static_configuration_only', runtime_verified=False,
                    detected_stacks=self.detected_stacks, existing_configs=self.existing_configs,
                    scanned_files_count=self.scanned_files_count,
                    critical_leaks_count=self.critical_leaks_count,
                    potential_context_tokens=self.potential_context_tokens,
                    configuration_errors=self.configuration_errors,
                    limitations=self.limitations, leaks=[x.to_dict() for x in self.leaks])


def audit_repository(repo_path: Path, target_names: Optional[List[str]] = None,
                     check_lockfiles=True, deep_scan=False):
    settings = load_settings(repo_path)
    targets = validate_targets(target_names if target_names is not None else settings.targets)
    if not repo_path.is_dir():
        raise ValueError(f'Not a directory: {repo_path}')
    report = AuditReport(repo_path, detect_project_stacks(repo_path), {}, 0)
    report.project = settings.to_dict()
    report.fail_on = settings.fail_on
    patterns = read_policy(repo_path)
    configured = {}
    for target in targets:
        filename = TARGET_FILENAME_MAP[target]
        report.existing_configs[filename] = (repo_path / filename).is_file()
        try:
            configured[target] = configured_patterns(repo_path, target)
            if not report.existing_configs[filename]:
                report.configuration_errors.append(f'{target}: missing {filename}')
        except (ValueError, OSError, TypeError, AttributeError) as exc:
            configured[target] = []
            report.configuration_errors.append(f'{target}: {exc}')
    git_rules = IgnoreRuleSet.from_file(repo_path / '.gitignore')
    for root, dirs, files in os.walk(repo_path, followlinks=False, onerror=lambda error: report.configuration_errors.append(f'Cannot traverse directory: {error.filename}')):
        for directory in dirs:
            if (Path(root) / directory).is_symlink():
                report.configuration_errors.append(f'Symlink directory not inspected: {(Path(root) / directory).relative_to(repo_path)}')
        dirs[:] = [d for d in dirs if d not in {'.git', '.hg', '.svn', '.codex'}
                   and not (Path(root) / d).is_symlink()]
        for filename in files:
            path = Path(root) / filename
            rel = path.relative_to(repo_path).as_posix()
            if rel in {'.agentignore', '.agentignore.toml', '.agentignore-baseline.json', '.gitignore'}:
                continue
            report.scanned_files_count += 1
            if path.is_symlink():
                report.configuration_errors.append(f'Symlink not inspected: {rel}')
                continue
            try:
                size = path.stat().st_size
                category = ('sensitive' if is_sensitive_path(rel) else
                            'policy' if covers(patterns, rel) else
                            'bloat' if is_bloat_path(rel) else
                            'lockfile' if check_lockfiles and is_lockfile_path(rel) else
                            'git_ignored' if git_rules.matches(rel) else None)
                content = scan_file_content(path) if deep_scan else []
                if content:
                    category = 'content_secret'
                if not category:
                    continue
                missing = [TARGET_FILENAME_MAP[t] for t in targets if not covers(configured[t], rel)]
                # Deep findings remain visible even when an access rule covers the file.
                if not missing and not content:
                    continue
                severity = 'CRITICAL' if category in {'sensitive', 'content_secret'} else 'HIGH' if category == 'policy' else 'MEDIUM'
                description = 'Path lacks a modeled project-local deny rule' if missing else 'Secret signature found in a configured path'
                if content:
                    description = '; '.join(f'{x.secret_type} on line {x.line_number} ({x.masked_sample})' for x in content)
                report.leaks.append(Leak(rel, category, severity,
                                         description, missing, size,
                                         max(1, size // 4) if is_text_file(path) else 0,
                                         content[0].line_number if content else None))
            except OSError as exc:
                report.configuration_errors.append(f'Cannot inspect {rel}: {exc}')
    report.leaks.sort(key=lambda item: (-SEVERITIES[item.severity.lower()], item.path, item.line_number or 0))
    return report
