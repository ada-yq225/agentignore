"""Personal workflow, gate/baseline semantics, safe previews and report regression tests."""
import json
from datetime import date
from pathlib import Path
import pytest
from agentignore.baseline import apply_baseline, create_baseline
from agentignore.cli import main
from agentignore.core import audit_repository, Leak
from agentignore.project import initialize_settings, load_settings
from agentignore.reports import render_html_report, sarif_report
from agentignore.syncer import plan_repository, sync_repository


def test_personal_settings_honor_single_client_and_preset(tmp_path):
    initialize_settings(tmp_path, 'balanced', ['codex'], 'My side project')
    settings = load_settings(tmp_path)
    assert settings.targets == ['codex']
    assert settings.preset == 'balanced'
    (tmp_path / 'dist').mkdir()
    (tmp_path / 'dist/app.js').write_text('generated')
    assert audit_repository(tmp_path).leaks[0].severity == 'HIGH'
    sync_repository(tmp_path)
    assert not (tmp_path / '.claude').exists()
    assert audit_repository(tmp_path).is_clean


@pytest.mark.parametrize('invalid', ['version=2', 'version=1\nunknown=true', 'version=1\n[check]\nfail_on="typo"',
                                    'version=1.0', 'version=true', 'version=1\n[project]\ntargets=["codex","claude"]',
                                    'version=1\n[policy]\npreset=[]', 'version=1\n[project]\ntargets=[]',
                                    'version=1\n[policy]\ndeny=["!unsafe"]'])
def test_settings_fail_closed(tmp_path, invalid):
    (tmp_path / '.agentignore.toml').write_text(invalid)
    with pytest.raises(ValueError):
        sync_repository(tmp_path)
    assert not (tmp_path / '.codex').exists()


def test_initialize_refuses_invalid_name_and_existing_file(tmp_path):
    with pytest.raises(ValueError):
        initialize_settings(tmp_path, name=' ')
    assert not (tmp_path / '.agentignore.toml').exists()
    initialize_settings(tmp_path)
    with pytest.raises(ValueError, match='already exists'):
        initialize_settings(tmp_path)


def test_advice_does_not_block_default_personal_gate(tmp_path):
    sync_repository(tmp_path)
    (tmp_path / 'yarn.lock').write_text('data')
    report = audit_repository(tmp_path)
    assert not report.is_clean
    assert not report.gate_failed()
    assert report.gate_failed('medium')


def test_explicit_policy_violation_blocks_gate(tmp_path):
    sync_repository(tmp_path)
    (tmp_path / '.agentignore').write_text('private/\n')
    (tmp_path / 'private').mkdir()
    (tmp_path / 'private/notes.txt').write_text('private')
    report = audit_repository(tmp_path)
    assert report.gate_failed()
    assert report.leaks[0].severity == 'HIGH'


def test_baseline_retains_findings_and_cannot_acknowledge_secrets(tmp_path):
    sync_repository(tmp_path)
    (tmp_path / 'yarn.lock').write_text('noise')
    (tmp_path / 'app.py').write_text('key="ghp_' + 'a' * 36 + '"')
    report = audit_repository(tmp_path, deep_scan=True)
    path = tmp_path / '.agentignore-baseline.json'
    data = create_baseline(report, path, 'Needed for dependency updates', '2026-10-20', date(2026, 10, 6))
    assert len(data['entries']) == 1
    apply_baseline(report, path, date(2026, 10, 6))
    assert len(report.leaks) == 2
    assert report.gate_failed('medium')
    assert not next(x for x in report.leaks if x.category == 'content_secret').accepted
    assert next(x for x in report.leaks if x.category == 'lockfile').accepted
    assert report.to_dict()['summary']['accepted'] == 1
    # Even a hand-edited baseline cannot suppress a critical finding.
    data['entries'].append(dict(id=report.leaks[0].finding_id, reason='malicious bypass', expires='2026-10-20'))
    path.write_text(json.dumps(data))
    apply_baseline(report, path, date(2026, 10, 6))
    assert not report.leaks[0].accepted


def test_expired_baseline_no_longer_affects_gate(tmp_path):
    sync_repository(tmp_path)
    (tmp_path / 'yarn.lock').write_text('noise')
    baseline = tmp_path / 'baseline.json'
    report = audit_repository(tmp_path)
    create_baseline(report, baseline, 'temporary', '2026-10-10', date(2026, 10, 6))
    apply_baseline(report, baseline, date(2026, 10, 8))
    assert not report.gate_failed('medium')
    apply_baseline(report, baseline, date(2026, 10, 11))
    assert report.gate_failed('medium')


@pytest.mark.parametrize(('reason','expires'), [('', '2026-10-10'), ('ok','2026-10-01'), ('ok','2027-10-01')])
def test_baseline_creation_requires_reason_and_bounded_expiry(tmp_path, reason, expires):
    report = audit_repository(tmp_path)
    with pytest.raises(ValueError):
        create_baseline(report, tmp_path / 'baseline.json', reason, expires, date(2026, 10, 6))


def test_dry_run_diff_does_not_expose_existing_config_values(tmp_path, capsys):
    (tmp_path / '.codex').mkdir()
    (tmp_path / '.codex/config.toml').write_text('model="PRIVATE_CONFIG_VALUE"')
    assert main(['sync', '--path', str(tmp_path), '--targets', 'codex', '--dry-run', '--diff']) == 0
    output = capsys.readouterr().out
    assert '**/.env' in output
    assert 'PRIVATE_CONFIG_VALUE' not in output
    assert (tmp_path / '.codex/config.toml').read_text() == 'model="PRIVATE_CONFIG_VALUE"'


def test_rule_ids_stable_when_config_coverage_changes(tmp_path):
    (tmp_path / 'app.py').write_text('key="ghp_' + 'a' * 36 + '"')
    first = audit_repository(tmp_path, deep_scan=True).leaks[0].finding_id
    sync_repository(tmp_path, ['codex'])
    second = audit_repository(tmp_path, deep_scan=True).leaks[0].finding_id
    assert first == second


def test_html_escapes_repository_content_and_replaces_tokens_once(tmp_path):
    report = audit_repository(tmp_path)
    report.project = {'name': '<script>alert(1)</script> __COUNT__'}
    report.leaks = [Leak('<img src=x onerror=alert(1)>', 'policy', 'HIGH', '</script><script>attack()</script>', [])]
    rendered = render_html_report(report.to_dict())
    assert '<script>alert(1)</script>' not in rendered
    assert '&lt;script&gt;alert(1)&lt;/script&gt; __COUNT__' in rendered
    assert '<img src=x' not in rendered
    assert 'connect-src \'none\'' in rendered
    assert 'aria-live="polite"' in rendered


def test_sarif_paths_encoded_and_configuration_errors_present(tmp_path):
    report = audit_repository(tmp_path)
    report.leaks = [Leak('src/file with space.py', 'content_secret', 'CRITICAL', 'Masked finding', [], line_number=4)]
    data = sarif_report(report.to_dict())
    run = data['runs'][0]
    assert data['version'] == '2.1.0'
    physical = run['results'][0]['locations'][0]['physicalLocation']
    assert physical['artifactLocation']['uri'] == 'src/file%20with%20space.py'
    assert physical['region']['startLine'] == 4
    assert run['invocations'][0]['executionSuccessful'] is False
    assert run['invocations'][0]['toolExecutionNotifications']


def test_cli_exports_html_and_enforces_selected_threshold(tmp_path):
    sync_repository(tmp_path)
    (tmp_path / 'yarn.lock').write_text('noise')
    output = tmp_path / 'report.html'
    assert main(['check', '--path', str(tmp_path), '--format', 'html', '--export', str(output)]) == 0
    assert '<!doctype html>' in output.read_text()
    assert main(['check', '--path', str(tmp_path), '--fail-on', 'medium']) == 1


def test_cli_json_gating_is_distinct_from_is_clean(tmp_path, capsys):
    sync_repository(tmp_path)
    (tmp_path / 'yarn.lock').write_text('noise')
    assert main(['check', '--path', str(tmp_path), '--json']) == 0
    data = json.loads(capsys.readouterr().out)
    assert not data['is_clean'] and not data['gate_failed']
    assert data['schema_version'] == '1.0'


def test_doctor_missing_clients_is_actionable_without_raw_output(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr('agentignore.doctor.shutil.which', lambda _: None)
    assert main(['doctor', '--path', str(tmp_path), '--json']) == 1
    report = json.loads(capsys.readouterr().out)
    assert report['clients'][0]['next_step'] == 'Install the client first'
    assert not report['runtime_verified']


def test_verify_does_not_pass_when_all_commands_fail(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from agentignore.verify import verify_codex
    sync_repository(tmp_path, ['codex'])
    monkeypatch.setattr('agentignore.verify.platform.system', lambda: 'Darwin')
    monkeypatch.setattr('agentignore.verify.shutil.which', lambda _: '/fake/codex')
    monkeypatch.setattr('agentignore.verify.subprocess.run', lambda *a, **kw: SimpleNamespace(returncode=1, stdout='', stderr='Operation not permitted'))
    result = verify_codex(tmp_path)
    assert not result['passed']
    assert not result['runtime_verified']


def test_verify_requires_actual_permission_denial(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from agentignore.verify import verify_codex
    sync_repository(tmp_path, ['codex'])
    monkeypatch.setattr('agentignore.verify.platform.system', lambda: 'Darwin')
    monkeypatch.setattr('agentignore.verify.shutil.which', lambda _: '/fake/codex')
    def run(command, **kwargs):
        if command[-1] == 'public.txt':
            return SimpleNamespace(returncode=0, stdout='AGENTIGNORE_PUBLIC_CANARY', stderr='')
        return SimpleNamespace(returncode=1, stdout='', stderr='configuration error')
    monkeypatch.setattr('agentignore.verify.subprocess.run', run)
    result = verify_codex(tmp_path)
    assert not result['passed']
    assert result['ordinary_session_verified'] is False


def test_anthropic_signature_is_not_misclassified_as_openai(tmp_path):
    from agentignore.scanner import scan_file_content
    path = tmp_path / 'app.py'
    path.write_text('key="sk-ant-' + 'x' * 35 + '"')
    found = scan_file_content(path)
    assert len(found) == 1 and found[0].secret_type == 'Anthropic API Key'


def test_only_codex_is_advertised_and_claude_config_is_untouched(tmp_path, capsys):
    from agentignore.constants import SUPPORTED_TARGETS
    assert list(SUPPORTED_TARGETS) == ['codex']
    path = tmp_path / '.claude/settings.json'
    path.parent.mkdir()
    path.write_text('{"personal":"unchanged"}')
    assert main(['sync', '--path', str(tmp_path)]) == 0
    assert path.read_text() == '{"personal":"unchanged"}'
    assert not path.with_name('settings.json.agentignore.bak').exists()
    capsys.readouterr()
    assert main(['sync', '--path', str(tmp_path), '--targets', 'claude', '--json']) == 2
    assert 'Supported targets: codex' in capsys.readouterr().out


def test_restore_preserves_original_and_current_configs(tmp_path):
    from agentignore.syncer import restore_repository
    path = tmp_path / '.codex/config.toml'
    path.parent.mkdir()
    original = '# original settings\nmodel="example"\n'
    path.write_text(original)
    path.chmod(0o600)
    sync_repository(tmp_path)
    managed = path.read_bytes()
    assert restore_repository(tmp_path, dry_run=True)['status'] == 'would_restore'
    assert path.read_bytes() == managed
    recovery = path.with_name('config.toml.agentignore.before-restore.bak')
    assert not recovery.exists()
    assert restore_repository(tmp_path)['status'] == 'restored'
    assert path.read_text() == original
    assert recovery.read_bytes() == managed
    assert path.with_name('config.toml.agentignore.bak').read_text() == original
    with pytest.raises(ValueError):
        restore_repository(tmp_path)
    assert path.read_text() == original


@pytest.mark.parametrize('obstacle', ['backup_symlink', 'temp', 'malformed', 'recovery'])
def test_restore_refuses_unsafe_inputs_without_mutation(tmp_path, obstacle):
    from agentignore.syncer import restore_repository
    path = tmp_path / '.codex/config.toml'
    path.parent.mkdir()
    path.write_text('model="original"')
    sync_repository(tmp_path)
    before = path.read_bytes()
    backup = path.with_name('config.toml.agentignore.bak')
    if obstacle == 'backup_symlink':
        backup.unlink()
        backup.symlink_to(tmp_path / 'outside')
    elif obstacle == 'malformed':
        backup.write_text('[broken')
    else:
        suffix = 'agentignore.tmp' if obstacle == 'temp' else 'agentignore.before-restore.bak'
        path.with_name('config.toml.' + suffix).write_text('existing')
    with pytest.raises((ValueError, OSError)):
        restore_repository(tmp_path)
    assert path.read_bytes() == before


def test_restore_missing_backup_and_stale_settings_are_actionable(tmp_path, capsys):
    sync_repository(tmp_path)
    assert main(['restore', '--path', str(tmp_path), '--json']) == 2
    assert 'first-write' in capsys.readouterr().out
    # Recover even when project preferences from a previous release need migration.
    path = tmp_path / '.codex/config.toml'
    path.with_name('config.toml.agentignore.bak').write_text('model="original"')
    (tmp_path / '.agentignore.toml').write_text('version=1\n[project]\ntargets=["claude"]')
    assert main(['restore', '--path', str(tmp_path), '--dry-run', '--json']) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'would_restore'
