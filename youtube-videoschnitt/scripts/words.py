"""Findet Wortfolgen im Transkript und gibt Quellzeit + Schnittzeit aus (für die Storyboard-Trigger).

    python3 words.py "Erster Win" "Link hier unten" "Parallax-Effekt"

Whisper-Zeiten sind ±0,3 s ungenau – für Einblendungen reicht das, für Schnitte nicht.
"""
import json, os, re, sys

w = json.load(open('transcript/transcript.json'))
tm = json.load(open('timemap.json')) if os.path.exists('timemap.json') else []
norm = lambda s: re.sub(r'[^\wäöüß-]', '', s.lower())
toks = [norm(x['text']) for x in w]


def S(t):
    for s, e, c, ty in tm:
        if t < s:
            return c
        if s <= t < e:
            return c + t - s
    return None


for phrase in sys.argv[1:]:
    p = [norm(x) for x in phrase.split()]
    hits = [round(w[i]['start'], 2) for i in range(len(toks) - len(p) + 1) if toks[i:i + len(p)] == p]
    print(f'{phrase!r}: ' + (', '.join(f'{h}s' + (f' (→ {S(h):.2f})' if tm else '') for h in hits) or 'nicht gefunden'))
