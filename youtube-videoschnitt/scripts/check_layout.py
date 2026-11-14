"""Positionsprüfung aller Einblendungen – Pflicht vor dem Rendern:

    python3 check_layout.py            # alle Segmente
    python3 check_layout.py m31 ff22   # nur diese

Misst jede Karte im echten Browser-Layout (rects.mjs) und meldet:
  RAND  – Karte (inkl. Icon) ragt über den Bildrand bzw. den Sicherheitsabstand (12 px)
  GESICHT – Karte liegt auf dem Gesicht/den Augen der Person (Vollbild: um layout.face; Split: im oberen Teil der Kamera)
Layout pro Zeitpunkt: split_2fps.npy (falls vorhanden, Quellzeit über timemap) sonst Segment-Art (th/sc).
"""
import json, os, re, subprocess, sys
import numpy as np

SK = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open('project.json'))
LAYOUT = CFG.get('layout', {})
man = json.load(open('manifest.json'))
TM = json.load(open('timemap.json'))
ids = sys.argv[1:] or [m['id'] for m in man if m['kind'] != 'end']
split = np.load('split_2fps.npy') if os.path.exists('split_2fps.npy') else None
M = 12


def src_of(t_out):
    for r in TM:
        sp = r[4] if len(r) > 4 else 1
        d = (r[1] - r[0]) / sp
        if r[2] <= t_out < r[2] + d:
            return r[0] + (t_out - r[2]) * sp
    return None


def layout_at(t_out, kind):
    if split is not None:
        s = src_of(t_out)
        if s is not None:
            return 'SC' if split[min(len(split) - 1, int(s * 2))] else 'TH'
    return 'TH' if kind == 'th' else 'SC'


fx, fy = LAYOUT.get('face', [0.5, 0.42])
# Listen wirken schnell „zu nah am Gesicht“ → Sperrzone inkl. Push-in-Zoom und Luft: ±390 px um die Gesichtsmitte
FACE_TH = (fx * 1920 - 390, fy * 1080 - 290, fx * 1920 + 390, fy * 1080 + 170)   # Stirn bis Kinn, Augen mittig, plus Abstand
cam = LAYOUT.get('cam') or {}
FACE_SC = ((cam['x'] + cam['w'] * .15, cam['y'] + cam['h'] * .12, cam['x'] + cam['w'] * .85, cam['y'] + cam['h'] * .58)
           if cam.get('shape') == 'rect' else None)

rects = json.loads(subprocess.run(['node', os.path.join(SK, 'rects.mjs')] + [f'segs/{i}' for i in ids],
                                  capture_output=True, text=True).stdout)
probs = 0
for m in man:
    if m['id'] not in rects:
        continue
    html = open(f'segs/{m["id"]}/index.html').read()
    for r in rects[m['id']]:
        cid = r['id']
        if r['x1'] - r['x0'] < 20 or r['y1'] - r['y0'] < 20:
            continue                                   # leere Hilfselemente
        a = re.search(r"tl\.fromTo\('#%s',.*?,(\d+(?:\.\d+)?)\);" % re.escape(cid), html)
        b = re.search(r"tl\.to\('#%s',\{opacity:0.*?,(\d+(?:\.\d+)?)\);" % re.escape(cid), html)
        t0 = float(a.group(1)) if a else 0.0
        t1 = float(b.group(1)) if b else m['dur']
        msg = []
        if r['x0'] < M or r['y0'] < M or r['x1'] > 1920 - M or r['y1'] > 1080 - M:
            msg.append(f"RAND ({r['x0']},{r['y0']})–({r['x1']},{r['y1']})")
        framed = f'id="{cid}-cam"' in html          # Learning/Kapitel im Vollbild: Person scharf im Rahmen, Hintergrund geblurrt → gewollt
        for tt in ([] if framed else np.linspace(t0, max(t0, t1), 5)):
            lay = layout_at(m['t0'] + tt, m['kind'])
            box = FACE_TH if lay == 'TH' else FACE_SC
            if box and r['x0'] < box[2] and r['x1'] > box[0] and r['y0'] < box[3] and r['y1'] > box[1]:
                msg.append(f'GESICHT ({lay}) bei {m["t0"] + tt:.1f}s')
                break
        if msg:
            probs += 1
            print(f"{m['id']:6s} {cid:14s} {m['t0'] + t0:7.1f}s  " + ' · '.join(msg))
print('OK – keine Probleme' if not probs else f'{probs} Einblendungen prüfen')
