"""Time-limited acknowledgements for low/medium noise; high risk cannot be hidden."""
import json
import re
from datetime import date
from pathlib import Path

BASELINE_FILE = '.agentignore-baseline.json'


def load_baseline(path: Path, today=None):
    today = today or date.today()
    if path.is_symlink():
        raise ValueError('Refusing symlink baseline')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('entries'), list):
        raise ValueError('Invalid baseline schema')
    entries = {}
    for entry in data['entries']:
        if not isinstance(entry, dict) or set(entry) != {'id', 'reason', 'expires'}:
            raise ValueError('Baseline entries require id, reason and expires')
        if not isinstance(entry['id'], str) or not re.fullmatch(r'[a-f0-9]{20}', entry['id']):
            raise ValueError('Invalid baseline finding id')
        if not isinstance(entry['reason'], str) or not entry['reason'].strip():
            raise ValueError('Baseline entries require a nonempty reason')
        expires = date.fromisoformat(entry['expires'])
        if entry['id'] in entries:
            raise ValueError('Duplicate baseline finding id')
        entries[entry['id']] = dict(entry, active=expires >= today)
    return entries


def create_baseline(report, path: Path, reason: str, expires: str, today=None):
    today = today or date.today()
    expiry = date.fromisoformat(expires)
    if not reason.strip() or expiry < today or (expiry - today).days > 90:
        raise ValueError('A reason and an expiry within 90 days are required')
    if path.exists() or path.is_symlink():
        raise ValueError('Baseline already exists; review and edit it explicitly')
    entries = [{'id': item.finding_id, 'reason': reason, 'expires': expires}
               for item in report.leaks if item.severity in ('MEDIUM', 'LOW')]
    data = dict(version=1, entries=entries)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    return data


def apply_baseline(report, path: Path, today=None):
    entries = load_baseline(path, today)
    for item in report.leaks:
        item.accepted = False
        item.acceptance_reason = None
        item.acceptance_expires = None
        entry = entries.get(item.finding_id)
        if entry and entry['active'] and item.severity in ('MEDIUM', 'LOW'):
            item.accepted = True
            item.acceptance_reason = entry['reason']
            item.acceptance_expires = entry['expires']
    return report
