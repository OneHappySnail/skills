import json, sys
from pathlib import Path
from string import Template

# Render template.md from a findings JSON. usage: fill.py findings.json out.md
# Output targets a Quill WYSIWYG paste: plain lines, "1."/"-" lists only. No tables, fences, emphasis or "#".
TBD = 'TBD by submitter'
SUBMITTER = {'site_id', 'severity', 'contact', 'environments_affected', 'users_affected', 'devices_affected', 'other_versions'}
REQUIRED = {'title', 'product', 'version', 'summary', 'problem', 'measurements', 'analysis', 'steps', 'questions', 'attachments'}


def table(t):
    # One bullet per row: "- <first col>: <col> = <val>; ...", or "- <a>: <b>" for two columns. n/a cells are dropped.
    cols = t['columns']
    if len(cols) == 2:
        return '\n'.join(f'- {a}: {b}' for a, b in t['rows'])
    return '\n'.join(f'- {r[0]}: ' + '; '.join(f'{c} = {v}' for c, v in zip(cols[1:], r[1:])
                                               if not str(v).startswith('n/a')) for r in t['rows'])


def analysis(items):
    out = []
    for n, i in enumerate(items, 1):
        out.append(f"{n}. {i['heading']} ({i['status']})\n\n{i['text']}")  # status: verified | inferred
        if i.get('excerpt'):
            out.append('Log excerpt:\n' + i['excerpt'].rstrip())
    return '\n\n'.join(out)


def render(f):
    missing = REQUIRED - {k for k, v in f.items() if v}
    if missing:
        sys.exit('missing required fields: ' + ', '.join(sorted(missing)))
    bad = [i['heading'] for i in f['analysis'] if i.get('status') not in ('verified', 'inferred')]
    if bad:
        sys.exit('analysis status must be verified|inferred: ' + ', '.join(bad))
    v = {k: f.get(k) or (TBD if k in SUBMITTER else 'None.') for k in
         ('title', 'site_id', 'severity', 'contact', 'product', 'version', 'platform', 'database',
          'environments_affected', 'users_affected', 'devices_affected', 'other_versions', 'summary', 'problem', 'impact', 'workarounds')}
    v['measurements'] = table(f['measurements'])
    v['analysis'] = analysis(f['analysis'])
    v['steps'] = '\n'.join(f'{n}. {s}' for n, s in enumerate(f['steps'], 1))
    v['questions'] = '\n'.join(f'{n}. {q}' for n, q in enumerate(f['questions'], 1))
    v['attachments'] = table(f['attachments'])
    return Template((Path(__file__).parent / 'template.md').read_text(encoding='utf-8')).substitute(v)


if __name__ == '__main__':
    findings = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    Path(sys.argv[2]).write_text(render(findings), encoding='utf-8')
    print(sys.argv[2])
