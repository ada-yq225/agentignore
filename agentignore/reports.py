"""Portable SARIF results and a self-contained, offline personal dashboard."""
import html
import json
from pathlib import Path
from urllib.parse import quote
from agentignore import __version__

RULES = {
    'AG001': ('Sensitive path lacks deny coverage', 'Review and synchronize permissions for credential-bearing files.'),
    'AG002': ('Hardcoded secret signature', 'Remove and, if real, rotate the credential.'),
    'AG003': ('Explicit policy path lacks deny coverage', 'Recompile the project policy and verify client configuration.'),
    'AG101': ('Potential context noise', 'Review optional exclusions for generated or dependency files.'),
    'AG102': ('Lockfile context recommendation', 'Keep lockfiles accessible if needed for dependency tasks.'),
    'AG103': ('Git exclusion differs from agent access', 'Review whether a Git exclusion should also restrict agent access.'),
}


def sarif_report(data):
    rules = [{'id': key, 'shortDescription': {'text': name}, 'help': {'text': help_text}}
             for key, (name, help_text) in RULES.items()]
    results = []
    for item in data['leaks']:
        location = {'artifactLocation': {'uri': quote(item['path'], safe='/'), 'uriBaseId': '%SRCROOT%'}}
        if item.get('line_number'):
            location['region'] = {'startLine': item['line_number']}
        result = dict(ruleId=item['rule_id'], level='error' if item['severity'] in ('CRITICAL', 'HIGH') else 'warning',
                      message={'text': item['description'] + ' ' + item['remediation']},
                      locations=[{'physicalLocation': location}],
                      partialFingerprints={'agentignore/v1': item['id']},
                      properties=dict(category=item['category'], severity=item['severity'], runtimeVerified=False))
        if item.get('accepted'):
            result['suppressions'] = [{'kind': 'external', 'status': 'accepted', 'justification': item['acceptance_reason']}]
        results.append(result)
    notifications = [{'level': 'error', 'message': {'text': error}} for error in data['configuration_errors']]
    return {'version': '2.1.0', '$schema': 'https://json.schemastore.org/sarif-2.1.0.json', 'runs': [{
        'tool': {'driver': {'name': 'agentignore', 'version': __version__,
                            'informationUri': 'https://github.com/ada-yq225/agentignore', 'rules': rules}},
        'results': results,
        'invocations': [{'executionSuccessful': not notifications,
                         'toolExecutionNotifications': notifications}],
        'properties': {'assessment': 'static_configuration_only', 'runtimeVerified': False,
                       'failOn': data['fail_on'], 'gateFailed': data['gate_failed']},
    }]}


def render_html_report(data):
    """User-controlled values are escaped; no remote assets or repository HTML executes."""
    esc = lambda text: html.escape(str(text), quote=True)
    name = data.get('project', {}).get('name', 'Personal project')
    cards = []
    for item in data['leaks']:
        accepted = bool(item.get('accepted'))
        searchable = ' '.join([item['path'], item['category'], item['severity']])
        cards.append(f'''<article class="finding" data-severity="{esc(item['severity'].lower())}" data-search="{esc(searchable.lower())}" data-accepted="{str(accepted).lower()}">
<div class="row"><span class="severity {esc(item['severity'].lower())}">{esc(item['severity'])}</span><span class="muted">{esc(item['rule_id'])} · {esc(item['category'])}</span><span class="tag">{'Acknowledged' if accepted else 'Needs review'}</span></div>
<h3>{esc(item['path'])}</h3><p>{esc(item['description'])}</p>
<div class="remedy"><span>Next step / 下一步</span><p>{esc(item['remediation'])}</p></div>
<p class="muted">Missing modeled coverage: {esc(', '.join(item['unshielded_targets']) or 'None — content finding remains actionable')}</p>
{('<p class="muted">Acknowledged until ' + esc(item.get('acceptance_expires')) + ': ' + esc(item.get('acceptance_reason')) + '</p>') if accepted else ''}
</article>''')
    errors = ''.join('<li>' + esc(item) + '</li>' for item in data['configuration_errors'])
    limits = ''.join('<li>' + esc(item) + '</li>' for item in data['limitations'])
    count = data['summary']['findings']
    blocker_count = sum(not item.get('accepted') and item['severity'] in ('CRITICAL', 'HIGH') for item in data['leaks'])
    # HTML lives offline; CSP blocks external resources and data exfiltration.
    template = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>agentignore · __NAME__</title><style>
:root{color-scheme:dark;--bg:#101419;--panel:#192129;--line:#2c3740;--muted:#a9b6c2;--text:#ecf2f6;--mint:#83e0bd}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:44px 28px}header{display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{font-size:23px;font-weight:750;letter-spacing:-1px}.brand span{color:var(--mint)}.pill,.tag{font-size:12px;padding:5px 10px;border:1px solid var(--line);border-radius:30px;color:var(--muted)}.eyebrow{color:var(--mint);font-size:12px;text-transform:uppercase;letter-spacing:2px;margin-top:48px}h1{font-size:clamp(32px,5vw,52px);line-height:1.1;letter-spacing:-2px;margin:12px 0;overflow-wrap:anywhere}h2{font-size:21px}h3{margin:12px 0 6px;font-size:19px;overflow-wrap:anywhere}p{margin:8px 0;color:#c5d0d9}.intro{max-width:750px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:28px 0}.stat{border:1px solid var(--line);background:var(--panel);border-radius:14px;padding:20px}.number{font-size:32px;font-weight:700;line-height:1.3}.label{color:var(--muted);font-size:13px}.notice{border-left:3px solid var(--mint);padding:14px 18px;background:#172720;border-radius:6px}.toolbar{display:flex;gap:12px;flex-wrap:wrap;margin:26px 0 14px}input,select{background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:8px;padding:12px;font:inherit}input[type=search]{flex:1;min-width:220px}label{display:flex;gap:8px;align-items:center;font-size:14px;color:var(--muted)}.finding{border:1px solid var(--line);border-radius:14px;padding:24px;margin:14px 0;background:var(--panel)}.row{display:flex;gap:12px;align-items:center;flex-wrap:wrap}.tag{margin-left:auto}.severity{font-size:11px;font-weight:800;letter-spacing:1px;padding:5px 9px;border-radius:5px}.critical{background:#4a252c;color:#ff9eab}.high{background:#473320;color:#f4c28b}.medium,.low{background:#273b4c;color:#a8caea}.muted{color:var(--muted);font-size:13px}.remedy{border-top:1px solid var(--line);margin-top:18px;padding-top:16px}.remedy>span{color:var(--mint);font-size:12px;font-weight:700}.empty{text-align:center;border:1px dashed var(--line);padding:36px;border-radius:14px}details{border:1px solid var(--line);border-radius:12px;padding:18px;margin:18px 0}summary{cursor:pointer;font-weight:600}li{color:var(--muted);margin:8px 0}code{background:#25312c;color:var(--mint);padding:3px 6px;border-radius:4px}footer{border-top:1px solid var(--line);margin-top:32px;padding:20px 0;color:var(--muted);font-size:12px}[hidden]{display:none!important}@media(max-width:650px){main{padding:24px 16px}.stats{grid-template-columns:repeat(2,1fr)}header{align-items:flex-start}.finding{padding:18px}.tag{margin-left:0}}
</style></head><body><main><header><div class="brand">agent<span>ignore</span></div><span class="pill">Local report · No uploads</span></header>
<div class="eyebrow">Personal project check / 个人项目体检</div><h1>__NAME__</h1><p class="intro">Understand what needs attention before your next Codex or Claude session. Review each finding, preview the changes, and verify your client's permissions.</p>
<div class="stats"><div class="stat"><div class="number">__BLOCKERS__</div><div class="label">High / critical to review</div></div><div class="stat"><div class="number">__COUNT__</div><div class="label">Total findings</div></div><div class="stat"><div class="number">__ERRORS__</div><div class="label">Configuration / scan errors</div></div><div class="stat"><div class="number">__SCANNED__</div><div class="label">Files inspected</div></div></div>
<div class="notice"><strong>__GATE__</strong><p>Threshold: __THRESHOLD__. Runtime enforcement has not been verified. Passing this check is not a security guarantee.</p></div>
<h2>Your next steps / 你的下一步</h2><p>1. Review the findings below. 2. Run <code>agentignore sync --dry-run</code> to preview policy changes. 3. Sync, restart your client, and verify a harmless canary.</p>
<details __ERROROPEN__><summary>Configuration and scan errors (__ERRORS__)</summary><ul>__ERRORLIST__</ul></details>
<div class="toolbar"><input id="search" type="search" aria-label="Search findings" placeholder="Search a file or category…"><select id="severity" aria-label="Filter severity"><option value="all">All severities</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select><label><input id="accepted" type="checkbox" checked>Show acknowledged</label></div>
<p id="visible" class="muted" aria-live="polite"></p><section id="findings">__CARDS__</section><p id="empty" class="empty" hidden>No matching findings. Check the filters and configuration errors above.</p>
<details><summary>What this report can and cannot tell you</summary><ul>__LIMITS__</ul></details>
<footer>agentignore __VERSION__ · Offline snapshot · Source code and credential values are not embedded. Filenames and masked findings can still be sensitive; review before sharing.</footer>
</main><script>
const search=document.getElementById('search'),severity=document.getElementById('severity'),accepted=document.getElementById('accepted'),cards=[...document.querySelectorAll('.finding')];
function filter(){let count=0;for(const card of cards){const show=card.dataset.search.includes(search.value.toLowerCase())&&(severity.value==='all'||severity.value===card.dataset.severity)&&(accepted.checked||card.dataset.accepted!=='true');card.hidden=!show;if(show)count++}document.getElementById('visible').textContent=count+' of '+cards.length+' findings shown';document.getElementById('empty').hidden=count!==0}
for(const element of [search,severity,accepted])element.addEventListener('input',filter);filter();
</script></body></html>'''
    values = dict(NAME=esc(name), BLOCKERS=str(blocker_count), COUNT=str(count), ERRORS=str(len(data['configuration_errors'])),
                  SCANNED=str(data['scanned_files_count']), GATE='Review required / 需要处理' if data['gate_failed'] else 'Threshold check passed / 达到检查阈值',
                  THRESHOLD=esc(data['fail_on']), ERROROPEN='open' if errors else '', ERRORLIST=errors or '<li>No configuration errors reported.</li>',
                  CARDS=''.join(cards), LIMITS=limits, VERSION=__version__)
    # One pass avoids interpreting placeholder-looking user input as template tokens.
    import re
    return re.sub(r'__([A-Z]+)__', lambda match: values[match.group(1)], template)


def export_sarif_report(data, path: Path):
    path.write_text(json.dumps(sarif_report(data), indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def export_html_report(data, path: Path):
    path.write_text(render_html_report(data), encoding='utf-8')
