"""Validated, versioned personal project settings. Unknown keys fail explicitly."""
from dataclasses import dataclass, field
from pathlib import Path
import tomlkit

SETTINGS_FILE = '.agentignore.toml'
PRESETS = {
    'secrets': [],
    'balanced': ['node_modules/', '.venv/', 'venv/', '__pycache__/', 'dist/', 'build/', '.next/', 'coverage/'],
}
SEVERITIES = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}


@dataclass
class ProjectSettings:
    name: str = 'Personal project'
    preset: str = 'secrets'
    targets: list = field(default_factory=lambda: ['codex'])
    deny: list = field(default_factory=list)
    fail_on: str = 'high'

    def to_dict(self):
        return dict(name=self.name, preset=self.preset, targets=self.targets, deny=self.deny, fail_on=self.fail_on)


def load_settings(root: Path) -> ProjectSettings:
    path = root / SETTINGS_FILE
    if path.is_symlink():
        raise ValueError(f'Refusing symlink settings: {SETTINGS_FILE}')
    if not path.exists():
        return ProjectSettings(name=root.name or 'Personal project')
    data = tomlkit.parse(path.read_text(encoding='utf-8'))
    if set(data) - {'version', 'project', 'policy', 'check'}:
        raise ValueError(f'Unknown top-level setting in {SETTINGS_FILE}')
    if not isinstance(data.get('version'), int) or isinstance(data.get('version'), bool) or data['version'] != 1:
        raise ValueError(f'{SETTINGS_FILE}: version must be 1')
    for section, keys in [('project', {'name', 'targets'}), ('policy', {'preset', 'deny'}), ('check', {'fail_on'})]:
        value = data.get(section, {})
        if not isinstance(value, dict) or set(value) - keys:
            raise ValueError(f'Invalid or unknown {section} setting in {SETTINGS_FILE}')
    settings = ProjectSettings(
        name=data.get('project', {}).get('name', root.name),
        targets=data.get('project', {}).get('targets', ['codex']),
        preset=data.get('policy', {}).get('preset', 'secrets'),
        deny=data.get('policy', {}).get('deny', []),
        fail_on=data.get('check', {}).get('fail_on', 'high'),
    )
    return _validate(settings)


def _validate(settings):
    if not isinstance(settings.name, str) or not settings.name.strip() or len(settings.name) > 120:
        raise ValueError('project.name must contain 1–120 characters')
    if not isinstance(settings.targets, list) or not settings.targets or any(x not in ('codex',) for x in settings.targets):
        raise ValueError('Only Codex is supported; set project.targets = ["codex"] in .agentignore.toml')
    if not isinstance(settings.preset, str) or settings.preset not in PRESETS:
        raise ValueError('policy.preset must be secrets or balanced')
    if not isinstance(settings.deny, list) or any(not isinstance(x, str) for x in settings.deny):
        raise ValueError('policy.deny must be an array of strings')
    if not isinstance(settings.fail_on, str) or settings.fail_on not in SEVERITIES:
        raise ValueError('check.fail_on must be critical, high, medium or low')
    from agentignore.policy import normalize_pattern
    for pattern in settings.deny:
        normalize_pattern(pattern)
    return settings


def initialize_settings(root: Path, preset='secrets', targets=None, name=None, dry_run=False):
    if preset not in PRESETS:
        raise ValueError('Unknown preset')
    path = root / SETTINGS_FILE
    if path.exists() or path.is_symlink():
        raise ValueError(f'{SETTINGS_FILE} already exists; use policy show and edit it explicitly')
    settings = _validate(ProjectSettings(name=name if name is not None else root.name, preset=preset, targets=targets if targets is not None else ['codex']))
    document = tomlkit.document()
    document.add(tomlkit.comment('Personal Codex policy. No source code or credentials are uploaded.'))
    document['version'] = 1
    document['project'] = {'name': settings.name, 'targets': settings.targets}
    document['policy'] = {'preset': settings.preset, 'deny': []}
    document['check'] = {'fail_on': settings.fail_on}
    text = tomlkit.dumps(document)
    if not dry_run:
        with path.open('x', encoding='utf-8') as stream:
            stream.write(text)
    return text
