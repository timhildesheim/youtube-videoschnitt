"""Synchronisiert die stumme „Kamera only“-Spur mit dem Hauptvideo – über das BILD, nicht über den Ton.

    python3 sync_cam.py "../Hauptvideo.mp4" "../… Kamera only.mp4" [--win a-b] [--win c-d] [--region x,y,w,h]

Idee: Die Bewegung der Person (Kopf, Mund, Hände) erzeugt in beiden Dateien denselben Verlauf der Bildänderung
(„Bewegungsenergie“ pro Frame). Kreuzkorrelation der beiden Verläufe → Versatz auf den Frame genau.
--win: Abschnitte des Hauptvideos (Sekunden), in denen die Kamera sichtbar ist – am besten Vollbild-Talking-Head
       am Anfang und am Ende (Standard: automatisch aus project.json → talking_head_ranges, erster und letzter).
--region: Kamerabereich im Hauptvideo in CSS-px (1920×1080), falls nur Split-Abschnitte verfügbar sind.
Ergebnis: camera_sync.json {offset_start, offset_end, drift_frames, confidence} – Kamerazeit = Hauptzeit + offset(t).
Zwei Fenster mit gleichem Versatz (±1 Frame) = keine Drift. Konfidenz < 2 → anderes Fenster wählen.
"""
import json, os, subprocess, sys
import numpy as np

FPS = 30
main, cam = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
wins = [tuple(map(float, args[i + 1].split('-'))) for i, a in enumerate(args) if a == '--win']
region = None
if '--region' in args:
    x, y, w, h = map(int, args[args.index('--region') + 1].split(','))
    region = (x * 2, y * 2, w * 2, h * 2)
if not wins and os.path.exists('project.json'):
    th = json.load(open('project.json')).get('talking_head_ranges', [])
    if th:
        a, b = th[0]
        wins.append((a + 2, min(b - 1, a + 92)))
        if len(th) > 1:
            a, b = th[-1]
            wins.append((max(a + 1, b - 91), b - 1))
assert wins, 'Bitte --win a-b angeben (Abschnitt, in dem die Kamera zu sehen ist)'
MAXLAG = 8.0  # Sekunden Suchbereich


def motion(path, t0, dur, crop=None):
    vf = (f'crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]},' if crop else '') + 'scale=96:54,format=gray'
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{max(0, t0):.3f}', '-t', f'{dur:.3f}', '-i', path,
                          '-vf', vf, '-r', str(FPS), '-f', 'rawvideo', '-'], capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, 54, 96).astype(np.float32)
    e = np.abs(np.diff(f, axis=0)).mean((1, 2))
    e = e - np.convolve(e, np.ones(15) / 15, 'same')   # langsame Helligkeitsänderungen entfernen
    return (e - e.mean()) / (e.std() + 1e-6)


res = []
for a, b in wins:
    m = motion(main, a, b - a, region)
    c = motion(cam, a - MAXLAG, (b - a) + 2 * MAXLAG)
    pre = int(round(max(0.0, MAXLAG - a) * FPS))   # Suchbereich vor Sekunde 0 → mit Nullen auffüllen
    if pre:
        c = np.concatenate([np.zeros(pre, np.float32), c])
    L = int(MAXLAG * FPS)
    scores = np.array([np.dot(m, c[k:k + len(m)]) / len(m) for k in range(0, 2 * L + 1) if k + len(m) <= len(c)])
    k = int(np.argmax(scores))
    lag = (k - L) / FPS                                   # Kamerazeit = Hauptzeit + lag
    if 0 < k < len(scores) - 1:                           # Parabel durch die Nachbarn → Sub-Frame-Schätzung
        y0, y1, y2 = scores[k - 1], scores[k], scores[k + 1]
        sub = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-9)
    else:
        sub = 0.0
    srt = np.sort(scores)
    # Konfidenz: Abstand des Maximums zum zweitbesten Wert außerhalb der direkten Nachbarschaft
    mask = np.ones(len(scores), bool)
    mask[max(0, k - 5):k + 6] = False
    conf = float((scores[k] - scores[mask].mean()) / (scores[mask].std() + 1e-6))
    res.append({'window': [a, b], 'offset': round(lag, 4), 'subframe': round(float(sub), 2), 'peak': round(float(scores[k]), 3), 'confidence': round(conf, 1)})
    print(f'Fenster {a:.0f}–{b:.0f}s: Kamera = Haupt {lag:+.3f}s ({k-L:+d} Frames, Feinwert {sub:+.2f}), Korrelation {scores[k]:.2f}, Konfidenz {conf:.1f}')

out = {'offset_start': res[0]['offset'], 'offset_end': res[-1]['offset'],
       't_start': sum(res[0]['window']) / 2, 't_end': sum(res[-1]['window']) / 2,
       'drift_frames': round((res[-1]['offset'] - res[0]['offset']) * FPS, 2),
       'confidence': min(r['confidence'] for r in res), 'windows': res}
json.dump(out, open('camera_sync.json', 'w'), indent=1)
print(f"Drift über das Video: {out['drift_frames']} Frames → camera_sync.json")
if abs(out['drift_frames']) > 1:
    print('⚠ Versatz ändert sich – weitere Fenster messen; Kamera-Einschübe nur dort setzen, wo der Versatz gemessen ist.')
if out['confidence'] < 3:
    print('⚠ Geringe Konfidenz – Fenster mit mehr Bewegung (Vollbild-Talking-Head, Gesten) wählen.')
if os.path.exists('project.json') and abs(out['drift_frames']) <= 1 and out['confidence'] >= 3:
    cfg = json.load(open('project.json'))
    cfg.setdefault('camera', {})
    cfg['camera'].update({'file': os.path.relpath(os.path.abspath(cam)), 'offset': out['offset_start']})
    cfg['camera'].setdefault('face', cfg.get('layout', {}).get('face', [0.5, 0.4]))  # nach dem OBS-Ausschnitt wie im Vollbild
    cfg.setdefault('camera_cuts', [])
    json.dump(cfg, open('project.json', 'w'), indent=1, ensure_ascii=False)
    print('project.json → camera.offset eingetragen')
