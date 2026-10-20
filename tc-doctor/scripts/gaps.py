import re, sys
from collections import defaultdict
from datetime import datetime

# Attribute wall time inside one request: gap to the next log line, summed by the (normalized) line before it.
# A large total behind one message means the step right after it is where time goes.
# usage: gaps.py file.syslog request-id [topN]
hdr = re.compile(r'^(\d{4}/\d\d/\d\d-\d\d:\d\d:\d\d\.\d{3}) UTC - \w+\s+- ([^-]*)- \S+ - \S* - (\S+) - (.*)$')
fmt = '%Y/%m/%d-%H:%M:%S.%f'
path, want = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 25

agg = defaultdict(lambda: [0, 0.0, 0.0])
prev = None
with open(path, encoding='utf-8', errors='replace') as f:
    for line in f:
        m = hdr.match(line)
        if not m or m.group(3) != want:
            continue
        t = datetime.strptime(m.group(1), fmt)
        if prev and t < prev[0]:  # libsyss timer lines carry second-truncated (.000) timestamps
            continue
        if prev:
            gap = (t - prev[0]).total_seconds()
            a = agg[prev[1]]; a[0] += 1; a[1] += gap; a[2] = max(a[2], gap)
        msg = re.sub(r'\b[A-Za-z0-9_$]{14}\b', 'UID', m.group(4))
        prev = (t, m.group(2).strip()[-28:] + ' | ' + re.sub(r'\d+', 'N', msg)[:140].strip())
total = sum(a[1] for a in agg.values())
print(f'total {total:.1f}s  (count | sum | max | line before gap)')
for k, (c, s, mx) in sorted(agg.items(), key=lambda kv: -kv[1][1])[:n]:
    print(f'{c:7} {s:9.1f} {mx:8.2f}  {k}')
