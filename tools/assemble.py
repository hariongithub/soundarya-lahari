import json, re, sys, collections
sys.path.insert(0, '/home/claude/sl-pdf')
from scanlib import scan_line, STD
from indic_transliteration import sanscript as S
built = json.load(open('built.json'))['verses']
kr = json.load(open('kr2.json'))
td = lambda t, to: S.transliterate(t, S.TELUGU, to)

# hand choices for lines where the two ebook sections disagree (A = verse-only section, B = commentary section)
CHOOSE_A = [(13,4),(14,1),(22,4),(23,4),(26,1),(55,4),(79,4),(83,2),(87,3),(90,1),(97,1)]
def tidy(l):
    l = l.replace('౽', 'ఽ'); l = re.sub(r'[।॥,.;:!?​﻿]', ' ', l); l = re.sub(r'[౦-౯0-9]+', ' ', l); return re.sub(r'\s+', ' ', l).strip()
def lines_of(ls): return [tidy(l) for l in ls if len(tidy(l).replace(' ', '')) >= 8]
OVER = {  # composed from the two sources plus the printed standard reading; flagged 'review'
    (14,3): 'దివి ద్విష్షట్త్రింశన్మనసి చ చతుఃషష్టిరితి యే',
    (15,3): 'సకృన్నత్వా నత్వా కథమివ సతాం సన్నిదధతే',
    (75,2): 'పయఃపారావారః పరివహతి సారస్వతమివ',
    (92,2): 'శివః స్వచ్ఛచ్ఛాయాఘటితకపటప్రచ్ఛదపటః',
    (31,1): 'చతుఃషష్ట్యా తన్త్రైః సకలమతిసన్ధాయ భువనం',
    (31,2): 'స్థితస్తత్తత్సిద్ధిప్రసవపరతన్త్రైః పశుపతిః',
    (53,1): 'విభక్తత్రైవర్ణ్యం వ్యతికలితలీలాఞ్జనతయా',
}
FIXLINES = {  # verses whose extracted line list was broken by page-break fragments
    31: [None, None, 'పున స్త్వన్నిర్బన్ధా దఖిలపురుషార్థైకఘటనా', 'స్వతన్త్రం తే తన్త్రం క్షితితలమవాతీతరదిదమ్'],
    53: [None, 'విభాతి త్వన్నేత్రత్రితయమిదమీశానదయితే', 'పునః స్రష్టుం దేవాన్ ద్రుహిణహరిరుద్రానుపరతాన్', 'రజః సత్త్వం బిభ్రత్ తమ ఇతి గుణానాం త్రయమివ'],
}
new = {}
for n in range(6, 101):
    v = built[str(n)]; lines = list(v['lines']); st = list(v['st'])
    if n in FIXLINES:
        lines = []; st = []
        for i, t in enumerate(FIXLINES[n]):
            lines.append(t or OVER[(n, i+1)]); st.append('review' if t is None else 'single-ok')
    for (m, i) in CHOOSE_A:
        if m == n:
            A = lines_of(kr[str(n)]['plain']); lines[i-1] = A[i-1]; st[i-1] = 'review'
    for (m, i), t in OVER.items():
        if m == n and n not in FIXLINES: lines[i-1] = t; st[i-1] = 'review'
    new[n] = (lines, st)

def level(st):
    if all(s in ('agree3', 'agree2') for s in st): return 'good'
    if any(s in ('review', 'single') for s in st): return 'review'
    return 'ok'

src = open('/home/claude/sl-site/index.html', encoding='utf-8').read()
i = src.index('const DATA = ') + len('const DATA = '); j = src.index(';\nconst SCAN')
data = json.loads(src[i:j])
for v in data: v['st'] = 'book'; v['lst'] = ['book'] * 4
SCAN = json.loads(src[src.index('const SCAN = ') + len('const SCAN = '):src.index(';\nconst YT')])
def part(n): return 'Ānandalaharī' if n <= 41 else 'Saundaryalaharī'
stats = collections.Counter(); failing = []
for n in range(6, 101):
    lines, st = new[n]
    dev = [td(l, S.DEVANAGARI) for l in lines]; rom = [td(l, S.IAST) for l in lines]
    lo = 6 + ((n - 6) // 5) * 5 if n <= 41 else 42 + ((n - 42) // 5) * 5
    hi = min(lo + 4, 41 if n <= 41 else 100)
    v = {'id': n, 'group': f'{part(n)}, verses {lo}–{hi}', 'dev': dev, 'rom': rom, 'tel': lines, 'mean': '', 'wbw': [], 'st': level(st), 'lst': st}
    data.append(v); stats[v['st']] += 1
    sc = []
    for li, d in enumerate(dev):
        syl, ok = scan_line(d)
        if len(syl) < 6: pause = {'dev': None, 'tel': None, 'rom': None}
        else:
            end = syl[5][4] + 1; pause = {'dev': end}
            for key, scr in (('tel', S.TELUGU), ('rom', S.IAST)):
                pre = S.transliterate(d[:end], S.DEVANAGARI, scr); full = v[key][li]
                pause[key] = len(pre) if full.startswith(pre) else None
        sc.append({'syl': [x[:4] for x in syl], 'pause': pause, 'ok': ok})
        if not ok: failing.append((n, li + 1, len(syl), ''.join(x[1] for x in syl)))
    SCAN[str(n)] = sc
print(stats, 'lines failing meter:', len(failing)); print(failing)
json.dump({'DATA': data, 'SCAN': SCAN}, open('final_data.json', 'w'), ensure_ascii=False)
