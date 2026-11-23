import json, re
from indic_transliteration import sanscript as S
CONS = set('कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळ')
IND = set('अआइईउऊऋॠऌएऐओऔ')
MAT = set('ािीुूृॄेैोौ')
LONG = set('ाीूॄेैोौआईऊॠएऐओऔ')
STD = "LGGGGGLLLLLGGLLLG"
def clean(line):
    line = re.sub(r'\([^)]*\)', '', line)           # drop bracketed alternative
    keep = []
    for k, ch in enumerate(line):
        if ch in CONS or ch in IND or ch in MAT or ch in 'ंः्ँ':
            keep.append((ch, k))
        elif keep and keep[-1][0] != '|':
            keep.append(('|', k))      # word or punctuation boundary
    return keep

def aksharas(keep):
    out = []; n = len(keep); p = 0
    while p < n:
        ch, k = keep[p]
        if ch in IND:
            a = {'cons': [], 'vowel': ch, 'start': k, 'mods': ''}; p += 1; end = k
        elif ch in CONS:
            cons = [ch]; start = k; p += 1; end = k
            while p + 1 < n and keep[p][0] == '्' and keep[p+1][0] in CONS:
                cons.append(keep[p+1][0]); end = keep[p+1][1]; p += 2
            if p < n and keep[p][0] == '्':   # final virama: coda
                out[-1]['coda'] += 1; out[-1]['end'] = keep[p][1]; p += 1
                continue
            vowel = 'अ'
            if p < n and keep[p][0] in MAT: vowel = keep[p][0]; end = keep[p][1]; p += 1
            a = {'cons': cons, 'vowel': vowel, 'start': start, 'mods': ''}
        else:
            p += 1; continue
        while p < n and keep[p][0] in 'ंः':
            a['mods'] += keep[p][0]; end = keep[p][1]; p += 1
        a['end'] = end; a['coda'] = 0
        out.append(a)
    return out

def scan_line(line):
    keep = clean(line); ak = aksharas(keep)
    syl = []
    for idx, a in enumerate(ak):
        text = line[a['start']:a['end']+1]
        nxt = ak[idx+1] if idx+1 < len(ak) else None
        reasons = []
        if a['vowel'] in LONG: reasons.append('long vowel')
        if 'ं' in a['mods']: reasons.append('followed by anusvāra (ṃ)')
        if 'ः' in a['mods']: reasons.append('followed by visarga (ḥ)')
        if a['coda']: reasons.append('followed by a closing consonant')
        if nxt and len(nxt['cons']) > 1:
            reasons.append('short vowel before the conjunct ' + '्'.join(nxt['cons'][:2]) + ('…' if len(nxt['cons']) > 2 else ''))
        act = 'G' if reasons else 'L'
        why = reasons[0] if reasons else 'short vowel, only one consonant after it'
        if act == 'G' and reasons[0] == 'long vowel': why = 'long vowel'
        syl.append([text, act, act, why, a['end']])
    last = syl[-1]
    if last[2] == 'L':
        last[1] = 'G'; last[3] = 'short here, but the last syllable of a line counts as heavy'
    elif idx_last_note := True:
        last[3] += ' (the last syllable of a line is free to count either way)'
    ok = len(syl) == 17 and all(x[1] == STD[k] for k, x in enumerate(syl))
    return syl, ok

