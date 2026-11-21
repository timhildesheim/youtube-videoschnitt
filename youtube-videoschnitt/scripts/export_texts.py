"""Schritt 12: Transkript des GESCHNITTENEN Videos exportieren (für Beschreibung, Kapitel, Notizen).

    python3 export_texts.py

Schreibt ../<profil.ablage.transkript_datei>: Sätze mit Zeitmarken (m:ss) des fertigen Videos.
Kapitel selbst festlegen und als ../<profil.ablage.kapitel_datei> ablegen (siehe references/description.md).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profil as PR
OUT = os.path.join('..', PR.get('ablage.transkript_datei') or 'Transkript-geschnitten.txt')

# Alle Wörter aus dem Original übernehmen: Whisper setzt Wortzeiten gern in Pausen, die der Schnitt entfernt hat –
# solche Wörter (die im Ton noch da sind) bekommen die Zeit des nächsten behaltenen Abschnitts statt zu verschwinden.
tm = json.load(open('timemap.json'))


def cut_time(t):
    for s, e, c, ty in tm:
        if t < s:
            return c
        if s <= t < e:
            return c + t - s
    return tm[-1][2] + tm[-1][1] - tm[-1][0]


OFF = json.load(open('project.json')).get('opener_sec', 0)   # Opener vorangestellt (assemble.py) → alles verschiebt sich
words = [{'text': x['text'], 'start': round(cut_time(x['start']) + OFF, 3)} for x in json.load(open('transcript/transcript.json'))]
lines, cur, st = [], [], None
for i, x in enumerate(words):
    st = x['start'] if st is None else st
    cur.append(x['text'])
    nxt = words[i + 1]['start'] if i + 1 < len(words) else None
    if x['text'].rstrip().endswith(('.', '?', '!')) or nxt is None or nxt - x['start'] > 2.5 or len(cur) > 35:
        t = int(st)
        lines.append(f'{t // 60}:{t % 60:02d}  {" ".join(cur)}')
        cur, st = [], None
open(OUT, 'w').write(
    'Transkript des fertig geschnittenen Videos (Zeitmarken passen zum finalen Video)\n\n' + '\n'.join(lines) + '\n')
print(f'{len(lines)} Zeilen → {OUT}')
