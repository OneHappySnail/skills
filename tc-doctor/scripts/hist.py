import re, sys
from collections import Counter

# Message histogram (digits/uids normalized) for one request id: hist.py file rid [topN]
path, rid = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 50
c = Counter()
inside = False
with open(path, encoding='utf-8', errors='replace') as f:
    for line in f:
        parts = line.split(' - ', 6)
        if len(parts) >= 7 and parts[0][:4].isdigit():
            inside = parts[5].strip() == rid
            if inside:
                msg = re.sub(r'\b[A-Za-z0-9_$]{14}\b', 'UID', parts[6])
                msg = re.sub(r'\d+', 'N', msg)[:150].strip()
                c[parts[1].strip()[:5] + ' ' + parts[3].strip()[-28:] + ' | ' + msg] += 1
        elif inside:
            c['(raw) ' + re.sub(r'\d+', 'N', line)[:120].strip()] += 1
for k, v in c.most_common(n):
    print(f'{v:7} {k}')
