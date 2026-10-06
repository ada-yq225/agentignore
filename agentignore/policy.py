"""A deliberately small, portable deny-policy language, not gitignore syntax."""
from pathlib import Path
import re
from functools import lru_cache
from agentignore.constants import SENSITIVE_PATTERNS


def normalize_pattern(pattern: str) -> str:
    # Negation/order cannot be translated to deny rules without changing meaning.
    if (not pattern or pattern.startswith(('!', '~', '#', '//')) or
            re.search(r'[\\\[\](){}\s]', pattern)):
        raise ValueError(f'Unsupported deny pattern: {pattern!r}; use paths, *, ? or ** only')
    anchored = pattern.startswith('/')
    pattern = pattern.lstrip('/')
    if any(part in ('', '.', '..') for part in pattern.rstrip('/').split('/')):
        raise ValueError(f'Unsafe deny pattern: {pattern!r}')
    if pattern.endswith('/'):
        pattern += '**'
    if not anchored and '/' not in pattern:
        pattern = '**/' + pattern
    # A directory basename applies at any depth, like a basename file pattern.
    elif not anchored and pattern.endswith('/**') and '/' not in pattern[:-3]:
        pattern = '**/' + pattern
    return pattern


def read_policy(repo_path: Path, include_lockfiles: bool = False):
    from agentignore.constants import LOCKFILE_PATTERNS
    from agentignore.project import PRESETS, load_settings
    settings = load_settings(repo_path)
    patterns = list(SENSITIVE_PATTERNS) + PRESETS[settings.preset] + settings.deny
    policy = repo_path / '.agentignore'
    if policy.is_symlink():
        raise ValueError('Refusing symlink input policy: .agentignore')
    if policy.exists():
        patterns += [line.strip() for line in policy.read_text(encoding='utf-8').splitlines()
                     if line.strip() and not line.lstrip().startswith('#')]
    if include_lockfiles:
        patterns += LOCKFILE_PATTERNS
    # Deduplication is safe only because this language has no negation or precedence.
    return list(dict.fromkeys(normalize_pattern(p) for p in patterns))


@lru_cache(maxsize=1024)
def _compile(pattern: str):
    """Compile once per pattern, with a bounded cache independent of repository size."""
    out, i = '', 0
    while i < len(pattern):
        if pattern[i:i+3] == '**/':
            out += '(?:.*/)?'
            i += 3
        elif pattern[i:i+2] == '**':
            out += '.*'
            i += 2
        elif pattern[i] == '*':
            out += '[^/]*'
            i += 1
        elif pattern[i] == '?':
            out += '[^/]'
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile('(?:' + out + r')\Z')


def matches(pattern: str, path: str) -> bool:
    return _compile(pattern).fullmatch(path.rstrip('/')) is not None
