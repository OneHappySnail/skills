import json, re, sys
from pathlib import Path
from string import Template

# Render template.md from a concept JSON. usage: fill.py concept.json out.md [--technical-only]
# --technical-only renders just the Technical Solution Concept section, for pasting into an existing document.
REQUIRED = {'topic', 'program', 'requirement_owner', 'leads', 'history', 'purpose', 'objectives',
            'business_context', 'scope', 'use_cases', 'ui', 'acceptance'}
STATUS = {'DRAFT', 'IN REVIEW', 'APPROVED'}
FREQUENCY = {'Very high', 'High', 'Medium', 'Low', 'One-time', 'Periodically', 'On demand'}
LEVEL = {'Low', 'Medium', 'High'}
OPEN = {'OPEN', 'IN PROGRESS', 'DONE'}
ACCEPTANCE = {'functional': ('F', 'Functional Acceptance'), 'technical': ('T', 'Integration & Technical Acceptance'),
              'user': ('U', 'User Acceptance'), 'data': ('D', 'Data Quality Acceptance')}
# Technical subsections in render order. Tuple = (heading, table columns or None).
TECH = {'architecture': ('Target Architecture Overview', ('Component', 'Role', 'TC Mechanism')),
        'data_model': ('Data Model Changes', None),
        'ui': ('UI and AWC Concept', None),
        'workflow': ('Workflow Design', None),
        'integration': ('Integration Concept', None),
        'external_sync': ('External Sync Concept', None),
        'processing': ('Processing Engine', None),
        'configuration': ('Configuration / Policy Model', None),
        'validation': ('Validation and Error Semantics', None),
        'persistence': ('Persistence and Runtime Behavior', None),
        'migration': ('Migration Concept', None),
        'separation': ('Separation of Concerns', ('Layer', 'Responsible for'))}


def fail(msg):
    sys.exit(msg)


def cell(v):
    return str(v).replace('|', '\\|').replace('\n', '<br>')


def table(cols, rows, name):
    for r in rows:
        if len(r) != len(cols):
            fail(f'{name}: row needs {len(cols)} cells {cols}: {r}')
    lines = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    return '\n'.join(lines + ['| ' + ' | '.join(cell(c) for c in r) + ' |' for r in rows])


def enum(v, allowed, name):
    if v not in allowed:
        fail(f'{name} must be one of {sorted(allowed)}: {v!r}')
    return v


def bullets(items):
    return '\n'.join(f'- {i}' for i in items)


def titled(items, numbered=False):
    # [{title, text}] -> "- **title**: text" (or "1. **title**: text")
    return '\n'.join(f"{f'{n}.' if numbered else '-'} **{i['title']}**: {i['text']}" for n, i in enumerate(items, 1))


def section(heading, body, level=3):
    return f"{'#' * level} {heading}\n\n{body}" if body else ''


def join(*parts):
    return '\n\n'.join(p for p in parts if p)


def objectives(items):
    return '\n'.join(f"{n}. **{o['title']}**\n" + '\n'.join(f'   - {p}' for p in o.get('points', []))
                     for n, o in enumerate(items, 1))


def scope(groups):
    return join(*(section(g['heading'], bullets(g['items']), 4) for g in groups)) or 'None.'


def use_cases(items):
    out = []
    for n, u in enumerate(items, 1):
        enum(u['frequency'], FREQUENCY, f'use case {n} frequency')
        out.append(join(f"### Use Case {n}: {u['title']}",
                        table(('Field', 'Description'), [('**Use Case**', u['title']), ('**Trigger**', u['trigger']),
                              ('**Business Outcome**', u['outcome']), ('**Frequency**', u['frequency'])], 'use case'),
                        f"**Use Case Narrative**\n\n{u['narrative']}",
                        f"**Business Rules**\n\n{bullets(u['rules'])}" if u.get('rules') else ''))
    return '\n\n'.join(out)


def ui(u):
    if not u.get('summary'):
        fail('ui.summary is required; state explicitly when there are no UI changes')
    return join(section('UX Change Summary', u['summary']),
                section('Current User Behavior', bullets(u.get('current', []))),
                section('Target User Behavior', bullets(u.get('target', []))),
                section('Resulting UX Impact', bullets(u.get('impact', []))),
                section('Required UI / Data Support', bullets(u.get('support', []))),
                section('Validation and Error Handling in UI', u.get('validation', '')))


def acceptance(a):
    unknown = set(a) - set(ACCEPTANCE)
    if unknown or not any(a.values()):
        fail(f'acceptance groups must be non-empty subset of {list(ACCEPTANCE)}: {sorted(unknown)}')
    return join(*(f'**{title}**\n\n' + table(('ID', 'Acceptance Criterion', 'Verification Method'),
                                               [(f'{p}{n}', *r) for n, r in enumerate(a[k], 1)], f'acceptance.{k}')
                  for k, (p, title) in ACCEPTANCE.items() if a.get(k)))


def technical(t):
    unknown = set(t) - set(TECH) - {'intro'}
    if unknown:
        fail(f'unknown technical subsections {sorted(unknown)}; allowed: {list(TECH)}')
    if not t.get('intro'):
        fail('technical.intro is required')
    parts = ['## Technical Solution Concept', t['intro']]
    for k, (heading, cols) in TECH.items():
        v = t.get(k)
        if not v:
            continue
        if cols:
            v = join(v.get('text', ''), table(cols, v['rows'], f'technical.{k}'))
        parts.append(section(heading, v))
    return join(*parts)


def render(f):
    missing = REQUIRED - {k for k, v in f.items() if v}
    if missing:
        fail('missing required fields: ' + ', '.join(sorted(missing)))
    v = {k: f[k] for k in ('topic', 'program', 'requirement_owner', 'purpose')}
    v['jira'] = '<br>'.join(f.get('jira', [])) or 'N/A'
    for k in ('working_groups', 'leads', 'contributors', 'approvers'):
        v[k] = cell(', '.join(f.get(k, [])) or 'TBD')
    v['status'] = enum(f.get('status', 'DRAFT'), STATUS, 'status')
    v['version'], v['created'] = f['history'][-1][0], f['history'][0][1]
    v['history'] = table(('Version', 'Date', 'Author', 'Change Description'), f['history'], 'history')
    v['objectives'] = objectives(f['objectives'])
    v['background'] = join(section('Business Context', f['business_context']),
                           section('Current Challenges', titled(f.get('challenges', []))),
                           section('Business Drivers', titled(f.get('drivers', []), numbered=True)),
                           section('Stakeholders', table(('Stakeholder', 'Role / Interest'), f['stakeholders'], 'stakeholders')
                                   if f.get('stakeholders') else ''))
    v['in_scope'] = scope(f['scope'].get('in', []))
    v['out_scope'] = scope(f['scope'].get('out', []))
    v['use_cases'] = use_cases(f['use_cases'])
    v['ui'] = ui(f['ui'])
    v['assumptions'] = table(('#', 'Assumption', 'Impact if False'),
                             [(f'A{n}', *r) for n, r in enumerate(f.get('assumptions', []), 1)], 'assumptions') \
        if f.get('assumptions') else 'None.'
    v['limitations'] = table(('Limitation', 'Description', 'Workaround / Handling'), f['limitations'], 'limitations') \
        if f.get('limitations') else 'None identified.'
    for n, r in enumerate(f.get('risks', []), 1):
        enum(r[1], LEVEL, f'risk {n} likelihood'), enum(r[2], LEVEL, f'risk {n} impact')
    v['risks'] = table(('Risk', 'Likelihood', 'Impact', 'Mitigation'), f['risks'], 'risks') if f.get('risks') else 'None identified.'
    v['acceptance'] = acceptance(f['acceptance'])
    v['technical'] = technical(f['technical']) if f.get('technical') else ''
    for n, r in enumerate(f.get('open_points', []), 1):
        enum(r[2], OPEN, f'open point {n} status')
    v['open_points'] = table(('Topic / Question / Decision', 'Responsible', 'Status'),
                             f.get('open_points') or [('None.', '', '')], 'open_points')
    out = Template((Path(__file__).parent / 'template.md').read_text(encoding='utf-8')).substitute(v)
    return re.sub(r'\n{3,}', '\n\n', out)


if __name__ == '__main__':
    concept = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    if '--technical-only' in sys.argv:
        if not concept.get('technical'):
            fail('missing required fields: technical')
        md = technical(concept['technical']) + '\n'
    else:
        md = render(concept)
    Path(sys.argv[2]).write_text(md, encoding='utf-8')
    print(sys.argv[2])
