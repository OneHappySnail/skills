import re, sys
from collections import defaultdict

# Group slow-SQL analyses by SQL_ID: count, total secs, rows, peeked binds, owning command.
hdr = re.compile(r'^(\S+) UTC - \w+\s+- [^-]*- \S+ - (\S*) - (\S+) - (.*)$')
took = re.compile(r'Took ([\d.]+) seconds to execute that SQL \(returning (\d+) rows')

for path in sys.argv[1:]:
    agg = defaultdict(lambda: dict(n=0, secs=0.0, rows=[], binds=set(), cmds=set(), text='', plan=''))
    pend = None  # (secs, rows, cmd) awaiting SQL_ID
    state = None
    sqlid = None
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = hdr.match(line)
            if m:
                state = None
                if pend:  # SQL text/plan is printed only for the first slow run of a SQL_ID
                    a = agg['(repeat, SQL not re-printed)']; a['n'] += 1; a['secs'] += pend[0]; a['rows'].append(pend[1]); a['cmds'].add(pend[2])
                    pend = None
                cmd = m.group(2)
                t = took.search(m.group(4))
                if t:
                    pend = (float(t.group(1)), int(t.group(2)), cmd)
                continue
            if pend and line.startswith('SQL_ID'):
                sqlid = line.split()[1].rstrip(',')
                a = agg[sqlid]; a['n'] += 1; a['secs'] += pend[0]; a['rows'].append(pend[1]); a['cmds'].add(pend[2])
                state = 'text'; pend = None
                continue
            if state == 'text':
                if line.startswith('---'):
                    continue
                if line.strip() == '':
                    state = None
                elif not agg[sqlid]['text'] or agg[sqlid]['n'] == 1:
                    if len(agg[sqlid]['text']) < 2000:
                        agg[sqlid]['text'] += line.strip() + ' '
            if sqlid and re.match(r'\s+\d+ - :\d+ \(', line):
                agg[sqlid]['binds'].add(line.split(':', 2)[-1].strip()[-40:])
            if sqlid and line.startswith('Plan hash value'):
                agg[sqlid]['plan'] = line.split(':')[1].strip()
    print('=== ' + path)
    for k, a in sorted(agg.items(), key=lambda kv: -kv[1]['secs']):
        rows = a['rows']
        print(f"{k} plan={a['plan']} n={a['n']} total={a['secs']:.0f}s avg={a['secs']/a['n']:.1f}s rows min/max={min(rows)}/{max(rows)} cmds={sorted(a['cmds'])}")
        print('   binds: ' + ' | '.join(sorted(a['binds']))[:400])
        print('   ' + a['text'][:700])
