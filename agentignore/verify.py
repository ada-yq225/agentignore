"""Explicit local Codex canary. Does not claim to verify ordinary sessions or all paths."""
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
import tomlkit
from agentignore.adapters import configured_patterns, load_config


def verify_codex(root: Path):
    if platform.system() != 'Darwin':
        raise ValueError('Automatic canary currently supports macOS only; use the documented manual test on other platforms')
    executable = shutil.which('codex')
    if not executable:
        raise ValueError('Install Codex before running the canary')
    configured_patterns(root, 'codex')  # Reject unknown inheritance and mixed/absolute overrides.
    config = load_config(root / '.codex/config.toml', 'codex')
    selected = config.get('default_permissions')
    profile = config.get('permissions', {}).get(selected)
    if not selected or not profile:
        raise ValueError('Sync a named Codex project profile first')
    with tempfile.TemporaryDirectory(prefix='agentignore-canary-') as directory:
        temporary = Path(directory).resolve()
        (temporary / '.codex').mkdir()
        isolated = tomlkit.document()
        isolated['default_permissions'] = selected
        isolated['permissions'] = {selected: profile}
        (temporary / '.codex/config.toml').write_text(tomlkit.dumps(isolated), encoding='utf-8')
        (temporary / 'public.txt').write_text('AGENTIGNORE_PUBLIC_CANARY', encoding='utf-8')
        (temporary / '.env.agentignore-canary').write_text('AGENTIGNORE_FAKE_SECRET_ONLY', encoding='utf-8')
        projects = tomlkit.inline_table()
        trust = tomlkit.inline_table()
        trust['trust_level'] = 'trusted'
        projects[str(temporary)] = trust
        command = [executable, 'sandbox', '-P', selected, '-C', str(temporary),
                   '-c', 'projects=' + projects.as_string(), '--', '/bin/cat']
        try:
            public = subprocess.run(command + ['public.txt'], cwd=temporary, capture_output=True, text=True, timeout=15)
            secret = subprocess.run(command + ['.env.agentignore-canary'], cwd=temporary, capture_output=True, text=True, timeout=15)
        except subprocess.TimeoutExpired as exc:
            raise ValueError('Codex canary timed out; runtime enforcement was not established') from exc
        readable = public.returncode == 0 and public.stdout == 'AGENTIGNORE_PUBLIC_CANARY'
        denied = (secret.returncode != 0 and not secret.stdout and
                  any(message in secret.stderr for message in ('Operation not permitted', 'Permission denied')))
        passed = readable and denied
        return dict(target='codex', passed=passed, public_read_success=readable, secret_read_denied=denied,
                    runtime_verified=passed, verification_scope='explicit_profile_fake_env_canary_on_macos',
                    ordinary_session_verified=False, all_policy_paths_verified=False,
                    limitations=['Tests a copy of the project profile in a temporary trusted project, selected explicitly.',
                                 'Does not establish original-project trust, inherited configuration or ordinary-session profile selection.',
                                 'No model/API calls, real credentials or persistent user configuration changes.'])
