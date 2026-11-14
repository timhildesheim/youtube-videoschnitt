"""Schritt 3: Schnittliste aus dem Tonpegel – Pausen kürzen, Versprecher entfernen.

Liest project.json:
  talking_head_ranges  [[a,b], …]   Vollbild-Talking-Head (Quellzeit) – dort straffer schneiden
  demo_ranges          [[a,b,keep]]  Stellen, an denen das BILD in der Pause zählt (Website-Scroll usw.)
  manual_remove        [[a,b], …]    Versprecher/Wiederholungen (Quellzeit, wird auf Pegelminimum gerastet)
  force_keep           [[a,b], …]    wird nie gekürzt (stille Lücken für eingeschobene Vollbild-Sequenzen)
  pause_keep           {'th':0.30,'sc':0.42}  so viel Pause bleibt stehen

Schreibt edl.json, timemap.json, voice_cut.wav (48 kHz, 6-ms-Blenden an jedem Schnitt),
words_cut.json und meldet, ob irgendwo lauter Ton weggeschnitten würde.
"""
import json, wave
import numpy as np

CFG = json.load(open('project.json'))
FPS = CFG.get('fps', 30)
DUR = CFG['duration']
TH = sorted(tuple(r) for r in CFG.get('talking_head_ranges', []) + CFG.get('camera_cuts', []))  # Kamera-Einschübe = Talking Head
DEMO = [tuple(r) for r in CFG.get('demo_ranges', [])]
MAN = [tuple(r) for r in CFG.get('manual_remove', [])]
PK = CFG.get('pause_keep', {'th': 0.30, 'sc': 0.42})

f = wave.open('audio16k.wav')
a = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32768
HOP = 160
k = len(a) // HOP
db = 20 * np.log10(np.sqrt((a[:k * HOP].reshape(k, HOP) ** 2).mean(1)) + 1e-9)
dbs = np.convolve(db, np.ones(5) / 5, 'same')

# Sprechschwelle relativ zum Sprachpegel (robust gegen leise/laute Aufnahmen)
speech_level = np.percentile(dbs[dbs > -70], 70)
THR = CFG.get('thr_db', speech_level - 14)          # thr_db: feste Schwelle, wenn leise Wortanfänge abgeschnitten werden
print(f'Sprachpegel ≈ {speech_level:.1f} dBFS → Schwelle {THR:.1f} dBFS')


def rtype(t):
    return 'TH' if any(x <= t < y for x, y in TH) else 'SC'


def maxkeep(t):
    for x, y, kp in DEMO:
        if x <= t < y:
            return kp
    return PK['th'] if rtype(t) == 'TH' else PK['sc']


voiced = dbs > THR
idx = np.flatnonzero(np.diff(np.r_[0, voiced.astype(int), 0]))
runs = [(idx[i] * 0.01, idx[i + 1] * 0.01) for i in range(0, len(idx), 2)]
merged = []
for s, e in runs:
    if merged and s - merged[-1][1] < 0.22:
        merged[-1] = (merged[-1][0], e)
    else:
        merged.append((s, e))
runs = [r for r in merged if r[1] - r[0] >= 0.06]


def snap(t, w=0.12):
    i0, i1 = max(0, int((t - w) * 100)), min(len(dbs) - 1, int((t + w) * 100))
    return (i0 + int(np.argmin(dbs[i0:i1 + 1]))) / 100


cuts, prev = [], 0.0
for s, e in runs + [(DUR, DUR)]:
    g, mk = s - prev, maxkeep((s + prev) / 2)
    if g > mk + 0.08 + 1e-6:   # Toleranz: Grenzfälle unabhängig von Gleitkomma-Rundung gleich entscheiden
        x, y = prev + mk * 0.6, s - mk * 0.4
        if prev == 0.0:
            x, y = 0.0, max(0, s - 0.35)
        if s >= DUR:
            x, y = prev + 0.8, DUR
        if y - x > 0.05:
            cuts.append((x, y))
    prev = e
cuts += [(snap(x), snap(y)) for x, y in MAN]
# force_keep: Bereiche, die nie gekürzt werden (z. B. stille Lücken für eingeschobene Vollbild-Sequenzen)
for fa, fb in CFG.get('force_keep', []):
    nc = []
    for x, y in cuts:
        if y <= fa or x >= fb:
            nc.append((x, y))
            continue
        if x < fa:
            nc.append((x, fa))
        if y > fb:
            nc.append((fb, y))
    cuts = nc
cuts.sort()
mc = []
for c in cuts:
    if mc and c[0] <= mc[-1][1]:
        mc[-1] = (mc[-1][0], max(mc[-1][1], c[1]))
    else:
        mc.append(c)
bounds = sorted(b for r in TH for b in r if 0 < b < DUR)
keep, t = [], 0.0
for x, y in mc:
    if x > t:
        keep.append((t, x))
    t = y
if t < DUR:
    keep.append((t, DUR))
qf = lambda x: round(round(x * FPS) / FPS, 4)
edl = []
for s, e in keep:
    pts = [s] + [b for b in bounds if s < b < e] + [e]
    for i in range(len(pts) - 1):
        a0, a1 = qf(pts[i]), qf(pts[i + 1])
        if a1 - a0 > 0.04:
            edl.append([a0, a1, rtype((a0 + a1) / 2)])
json.dump(edl, open('edl.json', 'w'))
kept = sum(e - s for s, e, _ in edl)
print(f'{len(edl)} Segmente · behalten {kept/60:.2f} min · entfernt {(DUR-kept)/60:.2f} min')

# Kontrolle: wurde lauter Ton (außer manuell) entfernt?
keptmask = np.zeros(k, bool)
for s, e, _ in edl:
    keptmask[int(s * 100):int(e * 100)] = True
loud = np.flatnonzero(~keptmask & (dbs > CFG.get('loud_db', speech_level - 8)))
man_mask = np.zeros(k, bool)
for x, y in MAN:
    man_mask[int((x - .3) * 100):int((y + .3) * 100)] = True
unexpected = [i / 100 for i in loud if not man_mask[i]]
print('Laute Stellen weggeschnitten (außer manuell):', len(unexpected), unexpected[:10])

# Zeitkarte + geschnittene Stimme
cum, tm = 0.0, []
for s, e, ty in edl:
    tm.append([s, e, round(cum, 4), ty])
    cum += (round(e * FPS) - round(s * FPS)) / FPS
json.dump(tm, open('timemap.json', 'w'))
f = wave.open('source_audio.wav')
sr, ch = f.getframerate(), f.getnchannels()
src = np.frombuffer(f.readframes(f.getnframes()), np.int16).reshape(-1, ch).astype(np.float32)
F = int(0.006 * sr)
ramp = np.linspace(0, 1, F)[:, None]
parts = []
for s, e, _ in edl:
    p = src[round(s * FPS) * sr // FPS: round(e * FPS) * sr // FPS].copy()
    p[:F] *= ramp
    p[-F:] *= ramp[::-1]
    parts.append(p)
o = wave.open('voice_cut.wav', 'wb')
o.setnchannels(ch); o.setsampwidth(2); o.setframerate(sr)
o.writeframes(np.clip(np.concatenate(parts), -32768, 32767).astype(np.int16).tobytes())
o.close()
words = json.load(open('transcript/transcript.json'))
wc = []
for x in words:
    for s, e, c, ty in tm:
        if s <= x['start'] < e:
            wc.append({'text': x['text'], 'start': round(c + x['start'] - s, 3), 'src': x['start'], 'ty': ty})
            break
json.dump(wc, open('words_cut.json', 'w'), ensure_ascii=False)
print(f'Neue Länge: {cum/60:.2f} min → timemap.json, voice_cut.wav')
