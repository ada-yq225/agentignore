"""Opt-in actual macOS sandbox test; no API calls or user config mutations."""
import os
import shutil
import subprocess
import sys
import pytest
import tomlkit
from agentignore.syncer import sync_repository


@pytest.mark.skipif(os.environ.get('AGENTIGNORE_RUN_CODEX_CANARY') != '1' or sys.platform != 'darwin' or not shutil.which('codex'),
                    reason='opt-in macOS Codex sandbox canary')
def test_generated_project_config_is_enforced(tmp_path):
    sync_repository(tmp_path, ['codex'])
    (tmp_path / 'public.txt').write_text('PUBLIC_CANARY')
    (tmp_path / '.env.agentignore-canary').write_text('FAKE_SECRET_CANARY')
    # Trust only this throwaway test project, using an invocation-local override.
    projects = tomlkit.inline_table()
    trust = tomlkit.inline_table()
    trust['trust_level'] = 'trusted'
    projects[str(tmp_path)] = trust
    command = ['codex', 'sandbox', '-P', 'agentignore', '-C', str(tmp_path),
               '-c', 'projects=' + projects.as_string(), '--', '/bin/cat']
    public = subprocess.run(command + ['public.txt'], cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert public.returncode == 0, public.stderr
    assert public.stdout == 'PUBLIC_CANARY'
    secret = subprocess.run(command + ['.env.agentignore-canary'], cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert secret.returncode != 0
    assert 'FAKE_SECRET_CANARY' not in secret.stdout
    assert 'Operation not permitted' in secret.stderr or 'Permission denied' in secret.stderr
