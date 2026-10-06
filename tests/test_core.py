"""Regression tests for static audit boundaries and dangerous false negatives."""
import json
import pytest
from agentignore.core import IgnoreRuleSet, audit_repository
from agentignore.syncer import sync_repository


def test_gitignore_negation_order():
    assert not IgnoreRuleSet(['*.log', '!important.log']).matches('important.log')


def test_input_file_cannot_shield_unconfigured_clients(tmp_path):
    (tmp_path / '.agentignore').write_text('.env\n')
    (tmp_path / '.env').write_text('DEMO=placeholder')
    report = audit_repository(tmp_path)
    assert not report.is_clean
    assert report.critical_leaks_count == 1
    assert report.leaks[0].unshielded_targets == ['.codex/config.toml', '.claude/settings.json']
    assert report.to_dict()['runtime_verified'] is False


def test_generated_settings_cover_root_and_nested_secrets(tmp_path):
    (tmp_path / 'src').mkdir()
    for file in (tmp_path / '.env', tmp_path / 'src' / '.env.local', tmp_path / 'src' / 'key.pem'):
        file.write_text('fake secret')
    sync_repository(tmp_path)
    report = audit_repository(tmp_path)
    assert report.is_clean
    assert report.to_dict()['assessment'] == 'static_configuration_only'
    assert report.limitations


def test_legacy_claudeignore_is_not_a_permission(tmp_path):
    (tmp_path / '.claudeignore').write_text('.env\n')
    (tmp_path / '.env').write_text('placeholder')
    assert not audit_repository(tmp_path, ['claude']).is_clean


def test_malformed_config_cannot_pass_empty_repo(tmp_path):
    (tmp_path / '.claude').mkdir()
    (tmp_path / '.claude/settings.json').write_text('{broken')
    report = audit_repository(tmp_path, ['claude'])
    assert not report.is_clean
    assert report.configuration_errors


def test_custom_policy_is_audited(tmp_path):
    (tmp_path / '.agentignore').write_text('internal/\n')
    (tmp_path / 'internal').mkdir()
    (tmp_path / 'internal/notes.txt').write_text('private')
    assert audit_repository(tmp_path).leaks[0].category == 'policy'


def test_deep_secret_reported_even_when_configured(tmp_path):
    (tmp_path / '.agentignore').write_text('app.py\n')
    (tmp_path / 'app.py').write_text('key="ghp_' + 'a' * 36 + '"')
    sync_repository(tmp_path)
    report = audit_repository(tmp_path, deep_scan=True)
    assert not report.is_clean
    assert report.leaks[0].category == 'content_secret'
    assert report.leaks[0].unshielded_targets == []


def test_binary_size_does_not_become_tokens(tmp_path):
    (tmp_path / 'bundle.bin').write_bytes(b'\x00' * 4000)
    (tmp_path / '.agentignore').write_text('*.bin\n')
    assert audit_repository(tmp_path).potential_context_tokens == 0


def test_legacy_codex_mode_not_counted_as_deny_policy(tmp_path):
    sync_repository(tmp_path)
    path = tmp_path / '.codex/config.toml'
    path.write_text('sandbox_mode="danger-full-access"\n' + path.read_text())
    report = audit_repository(tmp_path)
    assert not report.is_clean
    assert 'override' in report.configuration_errors[0]


def test_codex_mixed_overrides_not_treated_as_protected(tmp_path):
    (tmp_path / '.codex').mkdir()
    (tmp_path / '.codex/config.toml').write_text('''default_permissions="custom"
[permissions.custom]
extends=":workspace"
[permissions.custom.filesystem.":workspace_roots"]
"secrets"="deny"
"secrets/open"="read"
''')
    assert audit_repository(tmp_path, ['codex']).configuration_errors


def test_unknown_target_rejected(tmp_path):
    with pytest.raises(ValueError, match='Supported targets'):
        audit_repository(tmp_path, ['cursor'])


def test_undefined_codex_profile_is_configuration_error(tmp_path):
    (tmp_path / '.codex').mkdir()
    (tmp_path / '.codex/config.toml').write_text('default_permissions="missing"')
    assert audit_repository(tmp_path, ['codex']).configuration_errors
