from agentignore.syncer import compute_ignore_diff, sync_repository


def test_diff_compares_input_policy_to_actual_config(tmp_path):
    assert '**/.env' in compute_ignore_diff(tmp_path)['missing_in_ai']
    sync_repository(tmp_path)
    for target in ('codex', 'claude'):
        assert compute_ignore_diff(tmp_path, target)['missing_in_ai'] == []
    (tmp_path / '.agentignore').write_text('/private/\n')
    assert 'private/**' in compute_ignore_diff(tmp_path)['missing_in_ai']
