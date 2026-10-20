import re, sys
from collections import defaultdict

# Aggregate journal function timings inside each top-level call matching op-regex.
# usage: jnl.py file.jnl op-regex [topN] [name-filter-regex]
ret = re.compile(r'^@\*[\d.]*\s+(?:.*?\s)?(\S[^(]*?) returns .*?\[in ([\d.e+-]+) secs(?: cpu ([\d.e+-]+) secs elapsed)?(?: ,(\d+) DB trips)?')
top_ret = re.compile(r'^@\* \D.* returns ')
path, op = sys.argv[1], re.compile(sys.argv[2])
n = int(sys.argv[3]) if len(sys.argv) > 3 else 40
flt = re.compile(sys.argv[4]) if len(sys.argv) > 4 else None

blocks, agg = [], None
with open(path, encoding='utf-8', errors='replace') as f:
    for line in f:
        if not line.startswith('@') and line.rstrip().endswith(' (') and op.search(line):
            agg = defaultdict(lambda: [0, 0.0, 0.0, 0])
            blocks.append([line.strip(), '(no top-level return: journal truncated?)', agg])
            continue
        if agg is None:
            continue
        if top_ret.match(line):
            blocks[-1][1] = line.strip()[:160]
            agg = None
            continue
        r = ret.match(line)
        if r:
            a = agg[r.group(1).strip()[:110]]
            a[0] += 1; a[1] += float(r.group(2)); a[2] += float(r.group(3) or 0); a[3] += int(r.group(4) or 0)

for i, (start, end, agg) in enumerate(blocks):
    print(f'=== #{i+1} {start[:100]}\n    {end}\n    (cpu | elapsed | calls | DBtrips | name; nested calls are double-counted)')
    items = [kv for kv in agg.items() if not flt or flt.search(kv[0])]
    for k, (c, cpu, el, t) in sorted(items, key=lambda kv: -max(kv[1][1], kv[1][2]))[:n]:
        print(f'{cpu:9.1f} {el:9.1f} {c:7} {t:8}  {k}')
