"""Compilation, preservation, idempotency, conflict and safety checks."""
import pytest
import tomlkit
from agentignore.syncer import sync_repository
from agentignore.policy import normalize_pattern, matches


def test_sync_documented_configs_and_idempotency(tmp_path):
    first = sync_repository(tmp_path)
    assert first == {'.codex/config.toml': 'created'}
    assert not (tmp_path / '.claudeignore').exists()
    config = tomlkit.parse((tmp_path / '.codex/config.toml').read_text())
    assert config['default_permissions'] == 'agentignore'
    assert config['permissions']['agentignore']['extends'] == ':workspace'
    assert config['permissions']['agentignore']['filesystem'][':workspace_roots']['**/.env'] == 'deny'
    assert all(value == 'unchanged' for value in sync_repository(tmp_path).values())


def test_preserves_existing_settings_and_first_backup(tmp_path):
    (tmp_path / '.codex').mkdir()
    path = tmp_path / '.codex/config.toml'
    original = '# Keep this comment\nmodel="example"\n[model_providers.custom]\nbase_url="https://example.invalid"\n'
    path.write_text(original)
    sync_repository(tmp_path)
    result = tomlkit.parse(path.read_text())
    assert result['model'] == 'example'
    assert result['model_providers']['custom']['base_url'] == 'https://example.invalid'
    assert '# Keep this comment' in path.read_text()
    assert path.with_name('config.toml.agentignore.bak').read_text() == original
    sync_repository(tmp_path)
    assert path.with_name('config.toml.agentignore.bak').read_text() == original


@pytest.mark.parametrize('conflict', ['sandbox_mode="workspace-write"', 'default_permissions=":read-only"', '[permissions.agentignore]\nextends=":workspace"'])
def test_codex_conflicts_fail_before_writing_config(tmp_path, conflict):
    (tmp_path / '.codex').mkdir()
    path = tmp_path / '.codex/config.toml'
    path.write_text(conflict)
    with pytest.raises(ValueError):
        sync_repository(tmp_path)
    assert path.read_text() == conflict
    assert not path.with_name('config.toml.agentignore.bak').exists()


def test_malformed_codex_preflight(tmp_path):
    (tmp_path / '.codex').mkdir()
    path = tmp_path / '.codex/config.toml'
    path.write_text('permissions="not-a-table"')
    with pytest.raises(ValueError):
        sync_repository(tmp_path)
    assert path.read_text() == 'permissions="not-a-table"'
    assert not path.with_name('config.toml.agentignore.bak').exists()


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
    outside.write_text('model="example"')
    (tmp_path / '.codex').mkdir()
    (tmp_path / '.codex/config.toml').symlink_to(outside)
    with pytest.raises(ValueError, match='symlink'):
        sync_repository(tmp_path)
    assert outside.read_text() == 'model="example"'


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
    (tmp_path / '.codex').mkdir()
    (tmp_path / '.codex/config.toml.agentignore.bak').symlink_to(tmp_path / 'nonexistent')
    with pytest.raises(ValueError, match='symlink backup'):
        sync_repository(tmp_path)
    assert not (tmp_path / '.codex/config.toml').exists()


def test_private_config_file_mode_preserved(tmp_path):
    import os
    import stat
    if os.name != 'posix':
        pytest.skip('POSIX file modes')
    (tmp_path / '.codex').mkdir()
    path = tmp_path / '.codex/config.toml'
    path.write_text('model="example"')
    path.chmod(0o600)
    sync_repository(tmp_path)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.with_name('config.toml.agentignore.bak').stat().st_mode) == 0o600


def test_broken_symlink_settings_refused(tmp_path):
    (tmp_path / '.codex').mkdir()
    path = tmp_path / '.codex/config.toml'
    path.symlink_to(tmp_path / 'missing.json')
    with pytest.raises(ValueError, match='symlink config'):
        sync_repository(tmp_path)
    assert path.is_symlink()
