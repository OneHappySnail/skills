import re, sys

# Per ME_align_line_from_ebom_to_mbom call: elapsed, whether IDIC callback ran, gap right after it.
# usage: idic.py file.jnl...
ts = re.compile(r'-->\s+([\d.]+)s')
el = re.compile(r'ME_align_line_from_ebom_to_mbom returns .*?cpu ([\d.]+) secs elapsed(?: ,(\d+) DB trips)?')
for path in sys.argv[1:]:
    rows, cur, after_idic, last_t = [], None, False, None
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('Internal-MfgBvrCore-2016-04-DataManagement::saveData3 ('):
                rows.append(('SAVE', 0, 0, 0, 0))
            if 'ME_align_line_from_ebom_to_mbom (' in line:
                cur = dict(idic=0, gap=0.0)
                continue
            if cur is None:
                continue
            m = ts.search(line)
            if m:
                t = float(m.group(1))
                if after_idic and last_t is not None:
                    cur['gap'] += t - last_t
                    after_idic = False
                last_t = t
            if "USER_is_chain_needed_for_idic_generation" in line:
                cur['idic'] += 1
                after_idic = True
            r = el.search(line)
            if r:
                rows.append(('ALIGN', float(r.group(1)), int(r.group(2) or 0), cur['idic'], cur['gap']))
                cur = None
    print('=== ' + path)
    blk = []
    for r in rows + [('SAVE', 0, 0, 0, 0)]:
        if r[0] == 'SAVE':
            if blk:
                n = len(blk); tot = sum(b[1] for b in blk); idic = sum(1 for b in blk if b[3]); gap = sum(b[4] for b in blk)
                fast = [b for b in blk if not b[3]]; slow = [b for b in blk if b[3]]
                print(f"  saveData3: aligns={n} total={tot:.0f}s withIDIC={idic} gapAfterIDIC={gap:.0f}s "
                      f"avg(IDIC)={sum(b[1] for b in slow)/max(len(slow),1):.2f}s avg(noIDIC)={sum(b[1] for b in fast)/max(len(fast),1):.2f}s "
                      f"DBtrips={sum(b[2] for b in blk)}")
            blk = []
        else:
            blk.append(r)
