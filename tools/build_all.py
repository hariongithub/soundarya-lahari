import json, re, glob, sys, collections
sys.path.insert(0, '/home/claude/sl-pdf')
from scanlib import scan_line, STD
from indic_transliteration import sanscript as S
from rapidfuzz import fuzz, process
todev = lambda t: S.transliterate(t, S.TELUGU, S.DEVANAGARI)

def canon(dev):
    s = re.sub(r'[^ऀ-ॿ]', '', dev)
    s = re.sub(r'[।॥०-९]', '', s)
    cls = {'ङ': 'कखगघ', 'ञ': 'चछजझ', 'ण': 'टठडढ', 'न': 'तथदध', 'म': 'पफबभ'}
    for n, cs in cls.items(): s = re.sub(n + '्(?=[' + cs + '])', 'ं', s)
    s = s.replace('ऽ', '').replace('ळ', 'ल')
    if s.endswith('म्'): s = s[:-2] + 'ं'
    return re.sub('ः$', '', s)
def canon2(c):
    c = re.sub('[ङञणनम]्(?=[क-ह])', 'ं', c)       # any nasal+virama before a consonant ~ anusvara (comparison only)
    c = re.sub('ं+', 'ं', c)
    return re.sub('ः|[सशष]्', '', c)

def tidy(l):
    l = l.replace('౽', 'ఽ')
    l = re.sub(r'[।॥,.;:!?​﻿]', ' ', l)
    l = re.sub(r'[౦-౯0-9]+', ' ', l)
    return re.sub(r'\s+', ' ', l).strip()
def lines_of(ls):
    out = []
    for l in ls:
        l = tidy(l)
        if len(l.replace(' ', '')) >= 8: out.append(l)
    return out

kr = json.load(open('kr2.json'))
# OCR lines (canonical)
ocr = []
for f in sorted(glob.glob('ocr/im-*.hin.txt')):
    for ln in open(f, encoding='utf-8').read().split('\n'):
        c = canon2(canon(ln))
        if len(c) >= 14: ocr.append(c)
print('ocr lines', len(ocr))

def meter_ok(dev):
    syl, ok = scan_line(dev); return ok
def best_ocr(c):
    m = process.extractOne(c, ocr, scorer=fuzz.ratio); return (m[0], m[1]) if m else ('', 0)

out = {}; stats = collections.Counter(); review = []
for n in range(6, 101):
    A = lines_of(kr[str(n)]['plain']); B = lines_of(kr[str(n)]['tika'])
    base = A if len(A) == 4 else (B if len(B) == 4 else A)
    verse = {'id': n, 'lines': [], 'st': []}
    if len(base) != 4:
        verse['broken'] = True
        review.append((n, 0, 'line count %d/%d' % (len(A), len(B)), A, B))
    for i in range(min(4, len(base))):
        a = A[i] if len(A) == 4 else None; b = B[i] if len(B) == 4 else None
        cands = [x for x in (a, b) if x]
        if not cands: cands = [base[i]]
        info = []
        for t in cands:
            d = todev(t); c = canon(d); L, sc = best_ocr(canon2(c)); info.append((t, d, c, meter_ok(d), sc))
        chosen = info[0]; status = 'review'
        if len(info) == 2 and canon2(info[0][2]) == canon2(info[1][2]):
            chosen = info[0] if info[0][3] or not info[1][3] else info[1]
            status = 'agree3' if chosen[4] >= 85 else 'agree2'
        elif len(info) == 2:
            ok = [x for x in info if x[3]]
            if len(ok) == 1: chosen = ok[0]; status = 'resolved-meter'
            elif len(ok) == 2:
                d = info[0][4] - info[1][4]
                if abs(d) >= 1.5: chosen = info[0] if d > 0 else info[1]; status = 'resolved-scan'
                else: chosen = info[0]; status = 'review'
            else: chosen = max(info, key=lambda x: x[4]); status = 'review'
        else:
            chosen = info[0]
            status = 'single-ok' if chosen[3] and chosen[4] >= 80 else ('single' if chosen[3] else 'review')
        if status == 'review': review.append((n, i + 1, [x[0] for x in info], [x[3] for x in info], [x[4] for x in info]))
        verse['lines'].append(chosen[0]); verse['st'].append(status); stats[status] += 1
    out[n] = verse
print(stats); print('review lines:', len(review))
json.dump({'verses': out, 'review': review}, open('built.json', 'w'), ensure_ascii=False)
