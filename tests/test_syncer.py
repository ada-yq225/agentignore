"""Compilation, preservation, idempotency, conflict and safety checks."""
import json
import pytest
import tomlkit
from agentignore.syncer import sync_repository
from agentignore.policy import normalize_pattern, matches


def test_sync_documented_configs_and_idempotency(tmp_path):
    first = sync_repository(tmp_path)
    assert first == {'.codex/config.toml': 'created', '.claude/settings.json': 'created'}
    assert not (tmp_path / '.claudeignore').exists()
    config = tomlkit.parse((tmp_path / '.codex/config.toml').read_text())
    assert config['default_permissions'] == 'agentignore'
    assert config['permissions']['agentignore']['extends'] == ':workspace'
    assert config['permissions']['agentignore']['filesystem'][':workspace_roots']['**/.env'] == 'deny'
    deny = json.loads((tmp_path / '.claude/settings.json').read_text())['permissions']['deny']
    assert 'Read(/**/.env)' in deny
    assert 'Edit(/**/.env)' in deny
    assert all(value == 'unchanged' for value in sync_repository(tmp_path).values())


def test_preserves_existing_settings_and_first_backup(tmp_path):
    (tmp_path / '.claude').mkdir()
    path = tmp_path / '.claude/settings.json'
    original = '{"model":"example", "permissions":{"allow":["Bash(pytest *)"], "deny":["WebFetch"]},"env":{"DEMO":"1"}}'
    path.write_text(original)
    (tmp_path / '.codex').mkdir()
    (tmp_path / '.codex/config.toml').write_text('# Keep this comment\nmodel="example"\n')
    sync_repository(tmp_path)
    result = json.loads(path.read_text())
    assert result['model'] == 'example'
    assert result['permissions']['allow'] == ['Bash(pytest *)']
    assert result['permissions']['deny'][0] == 'WebFetch'
    assert result['env'] == {'DEMO': '1'}
    assert path.with_name('settings.json.agentignore.bak').read_text() == original
    assert '# Keep this comment' in (tmp_path / '.codex/config.toml').read_text()
    sync_repository(tmp_path)
    assert path.with_name('settings.json.agentignore.bak').read_text() == original


@pytest.mark.parametrize('conflict', ['sandbox_mode="workspace-write"', 'default_permissions=":read-only"', '[permissions.agentignore]\nextends=":workspace"'])
def test_codex_conflicts_fail_before_writing_either_target(tmp_path, conflict):
    (tmp_path / '.codex').mkdir()
    path = tmp_path / '.codex/config.toml'
    path.write_text(conflict)
    with pytest.raises(ValueError):
        sync_repository(tmp_path, ['claude', 'codex'])
    assert path.read_text() == conflict
    assert not (tmp_path / '.claude').exists()


def test_malformed_claude_preflight(tmp_path):
    (tmp_path / '.claude').mkdir()
    (tmp_path / '.claude/settings.json').write_text('{"permissions":{"deny":"not-a-list"}}')
    with pytest.raises(ValueError):
        sync_repository(tmp_path)
    assert not (tmp_path / '.codex').exists()


def test_dry_run_writes_nothing(tmp_path):
    assert sync_repository(tmp_path, dry_run=True)
    assert list(tmp_path.iterdir()) == []


def test_policy_not_rewritten_and_gitignore_not_imported(tmp_path):
    policy = '# human-maintained\nprivate/\n'
    (tmp_path / '.agentignore').write_text(policy)
    (tmp_path / '.gitignore').write_text('*.log\n!safe.log\n')
    sync_repository(tmp_path)
    assert (tmp_path / '.agentignore').read_text() == policy
    assert 'safe.log' not in (tmp_path / '.codex/config.toml').read_text()


@pytest.mark.parametrize('pattern', ['!safe.log', '../outside', 'a/../b', '[ab].txt', 'a(b)', '~/secret', 'a\\b', '//tmp/x'])
def test_unsupported_patterns_fail_without_mutation(tmp_path, pattern):
    (tmp_path / '.agentignore').write_text(pattern + '\n')
    with pytest.raises(ValueError):
        sync_repository(tmp_path)
    assert not (tmp_path / '.codex').exists()


def test_symlink_target_not_followed(tmp_path):
    outside = tmp_path / 'original.json'
    outside.write_text('{}')
    (tmp_path / '.claude').mkdir()
    (tmp_path / '.claude/settings.json').symlink_to(outside)
    with pytest.raises(ValueError, match='symlink'):
        sync_repository(tmp_path)
    assert outside.read_text() == '{}'


@pytest.mark.parametrize(('pattern','yes','no'), [
    ('.env', ['.env','src/.env'], ['.env.example','a.env']),
    ('/private/', ['private/a','private/sub/b'], ['src/private/a']),
    ('private/', ['private/a','src/private/a'], ['private-file']),
    ('*.key', ['a.key','src/a.key'], ['a.keys']),
    ('config/*.json', ['config/a.json'], ['src/config/a.json','config/sub/a.json']),
])
def test_portable_pattern_semantics(pattern, yes, no):
    glob = normalize_pattern(pattern)
    assert all(matches(glob, x) for x in yes)
    assert not any(matches(glob, x) for x in no)


def test_backup_symlink_rejected_before_any_output(tmp_path):
    (tmp_path / '.claude').mkdir()
    (tmp_path / '.claude/settings.json.agentignore.bak').symlink_to(tmp_path / 'nonexistent')
    with pytest.raises(ValueError, match='symlink backup'):
        sync_repository(tmp_path)
    assert not (tmp_path / '.codex').exists()


def test_private_config_file_mode_preserved(tmp_path):
    import os
    import stat
    if os.name != 'posix':
        pytest.skip('POSIX file modes')
    (tmp_path / '.claude').mkdir()
    path = tmp_path / '.claude/settings.json'
    path.write_text('{}')
    path.chmod(0o600)
    sync_repository(tmp_path)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.with_name('settings.json.agentignore.bak').stat().st_mode) == 0o600


def test_broken_symlink_settings_refused(tmp_path):
    (tmp_path / '.claude').mkdir()
    path = tmp_path / '.claude/settings.json'
    path.symlink_to(tmp_path / 'missing.json')
    with pytest.raises(ValueError, match='symlink config'):
        sync_repository(tmp_path)
    assert path.is_symlink()
