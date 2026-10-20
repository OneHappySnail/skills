import re, sys
from datetime import datetime

# Per service request: wall span, client command, slow-SQL count/time, POM x-act count/time.
# usage: requests.py file.syslog [op-regex] [min-wall-secs]
hdr = re.compile(r'^(\d{4}/\d\d/\d\d-\d\d:\d\d:\d\d\.\d{3}) UTC - \w+\s+- [^-]*- \S+ - (\S*) - (\S+) - (.*)$')
slow = re.compile(r'Took ([\d.]+) seconds to execute that SQL')
xact = re.compile(r'^(\d+) seconds to POM DB x-act')
fmt = '%Y/%m/%d-%H:%M:%S.%f'

path = sys.argv[1]
op = re.compile(sys.argv[2]) if len(sys.argv) > 2 else None
minwall = float(sys.argv[3]) if len(sys.argv) > 3 else 0
reqs, rid = {}, None
with open(path, encoding='utf-8', errors='replace') as f:
    for line in f:
        m = hdr.match(line)
        if not m:
            x = xact.match(line)
            if x and rid in reqs:
                reqs[rid]['xact'].append(int(x.group(1)))
            continue
        t, cmd, rid, msg = m.groups()
        if 'Service Request:' in msg:
            reqs.setdefault(rid, dict(op=msg.split('Service Request:')[1].strip(), cmd=cmd, start=t, end=t, slow=[], xact=[]))
        r = reqs.get(rid)
        if r:
            r['end'] = t
            s = slow.search(msg)
            if s:
                r['slow'].append(float(s.group(1)))
for rid, r in reqs.items():
    wall = (datetime.strptime(r['end'], fmt) - datetime.strptime(r['start'], fmt)).total_seconds()
    if (op and not op.search(r['op'])) or wall < minwall:
        continue
    print(f"{r['start']} {rid} wall={wall:7.1f}s slowSQL={len(r['slow'])}/{sum(r['slow']):.0f}s "
          f"xact={len(r['xact'])}/{sum(r['xact'])}s {r['cmd'][:40]:40} {r['op']}")
