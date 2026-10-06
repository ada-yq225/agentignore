"""Read-only installation diagnostics. Never read user credentials or change trust."""
import platform
import re
import shutil
import subprocess
from pathlib import Path
from agentignore import __version__
from agentignore.adapters import configured_patterns
from agentignore.constants import TARGET_FILENAME_MAP
from agentignore.project import load_settings


def diagnose(root: Path, targets=None):
    settings = load_settings(root)
    result = dict(version=__version__, platform=platform.system(), project=settings.to_dict(),
                  runtime_verified=False, clients=[])
    for target in targets or settings.targets:
        executable = shutil.which(target)
        client = dict(target=target, installed=bool(executable), version=None,
                      config_file=TARGET_FILENAME_MAP[target], config_valid=False,
                      error=None, runtime_verified=False)
        if executable:
            try:
                process = subprocess.run([executable, '--version'], capture_output=True, text=True, timeout=5)
                match = re.search(r'\b\d+\.\d+\.\d+\b', process.stdout)
                client['version'] = match.group() if match and process.returncode == 0 else None
            except (OSError, subprocess.TimeoutExpired):
                client['error'] = 'Client version could not be read'
        try:
            patterns = configured_patterns(root, target)
            client['config_valid'] = (root / TARGET_FILENAME_MAP[target]).is_file() and bool(patterns)
            client['modeled_deny_patterns'] = len(patterns)
        except (ValueError, TypeError, OSError, AttributeError) as exc:
            client['error'] = str(exc)
        client['next_step'] = ('Install the client first' if not executable else
                               'Run agentignore sync --dry-run, then sync' if not client['config_valid'] else
                               'Restart the client; verify loaded permissions and a fake secret canary')
        result['clients'].append(client)
    return result
