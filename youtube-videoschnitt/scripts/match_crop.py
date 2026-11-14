"""Ermittelt den Bildausschnitt, mit dem die Aufnahmesoftware (z. B. OBS) die Rohkamera ins Vollbild setzt – damit Kamera-Einschübe genauso aussehen.

    python3 match_crop.py "../<Hauptvideo>.mp4" "../<… Kamera only>.mp4" 20 60 470 [weitere Zeitpunkte im Vollbild]

Zeitpunkte = Sekunden im Hauptvideo, an denen die OBS-Vollbild-Kamera zu sehen ist. Braucht camera.offset aus
sync_cam.py (project.json). Sucht Zoom + Position, bei denen der Rohkamera-Ausschnitt deckungsgleich mit dem
Hauptvideo ist (normierte Kreuzkorrelation über FFT, erst grob, dann fein). Schreibt camera.crop {x,y,w,h} in
Rohkamera-Pixeln nach project.json und meldet die Übereinstimmung je Zeitpunkt (> 0,9 = deckungsgleich).
"""
import json, subprocess, sys
import numpy as np

main, cam = sys.argv[1], sys.argv[2]
times = [float(t) for t in sys.argv[3:]] or [20.0]
cfg = json.load(open('project.json'))
off = cfg['camera']['offset']


def frame(path, t, w):
    h = w * 9 // 16
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.4f}', '-i', path, '-frames:v', '1',
                          '-vf', f'scale={w}:{h}:flags=area,format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w).astype(np.float64)


def resize(img, w, h):
    # bilineare Skalierung mit numpy (reicht für die Suche)
    ys = np.linspace(0, img.shape[0] - 1, h)
    xs = np.linspace(0, img.shape[1] - 1, w)
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    y1 = np.minimum(y0 + 1, img.shape[0] - 1); x1 = np.minimum(x0 + 1, img.shape[1] - 1)
    fy = (ys - y0)[:, None]; fx = (xs - x0)[None, :]
    a = img[np.ix_(y0, x0)]; b = img[np.ix_(y0, x1)]; c = img[np.ix_(y1, x0)]; d = img[np.ix_(y1, x1)]
    return a * (1 - fy) * (1 - fx) + b * (1 - fy) * fx + c * fy * (1 - fx) + d * fy * fx


def ncc_map(big, tpl):
    """Normierte Kreuzkorrelation von tpl über allen gültigen Positionen in big (FFT)."""
    th, tw = tpl.shape
    t = tpl - tpl.mean(); tn = np.sqrt((t ** 2).sum())
    H, Wd = big.shape[0] + th, big.shape[1] + tw
    F = np.fft.rfft2(big, (H, Wd)) * np.conj(np.fft.rfft2(t, (H, Wd)))
    corr = np.fft.irfft2(F, (H, Wd))[:big.shape[0] - th + 1, :big.shape[1] - tw + 1]
    s1 = np.cumsum(np.cumsum(np.pad(big, ((1, 0), (1, 0))), 0), 1)
    s2 = np.cumsum(np.cumsum(np.pad(big ** 2, ((1, 0), (1, 0))), 0), 1)
    def box(s):
        return s[th:, tw:] - s[:-th, tw:] - s[th:, :-tw] + s[:-th, :-tw]
    n = th * tw
    var = box(s2) - box(s1) ** 2 / n
    return corr / (np.sqrt(np.maximum(var, 1e-6)) * tn)


def search(m, c, scales, base_w):
    """m: Hauptvideo-Frame (base_w breit), c: Rohkamera (gleiche Auflösung). Zoom s → Kamera auf base_w*s skalieren."""
    best = (-1, None)
    for s in scales:
        cw = int(round(base_w * s)); ch = int(round(cw * 9 / 16))
        big = resize(c, cw, ch)
        r = ncc_map(big, m)
        k = np.unravel_index(np.argmax(r), r.shape)
        if r[k] > best[0]:
            best = (float(r[k]), (s, k[1], k[0]))
    return best


results = []
for t in times:
    m1, c1 = frame(main, t, 320), frame(cam, t + off, 320)
    sc, (s, x, y) = search(m1, c1, np.arange(1.0, 1.81, 0.01), 320)
    m2, c2 = frame(main, t, 640), frame(cam, t + off, 640)          # Feinsuche
    sc2, (s2, x2, y2) = search(m2, c2, np.arange(s - 0.012, s + 0.0121, 0.002), 640)
    # Ausschnitt in Rohkamera-Pixeln (3840 breit)
    w = 3840 / s2; h = w * 9 / 16
    cx = x2 / (640 * s2) * 3840; cy = y2 / (360 * s2) * 2160
    results.append((sc2, cx, cy, w, h))
    print(f'{t:7.1f}s: Zoom {s2:.3f} · Ausschnitt x={cx:.0f} y={cy:.0f} w={w:.0f} h={h:.0f} · Übereinstimmung {sc2:.3f}')

good = [r for r in results if r[0] > 0.85]
assert good, 'Keine deckungsgleiche Stelle gefunden – Zeitpunkte im OBS-Vollbild wählen'
med = np.median(np.array([r[1:] for r in good]), axis=0)
x, y, w, h = (int(round(v / 2) * 2) for v in med)                  # gerade Werte für ffmpeg
cfg['camera']['crop'] = {'x': x, 'y': y, 'w': w, 'h': h}
json.dump(cfg, open('project.json', 'w'), indent=1, ensure_ascii=False)
print(f'camera.crop = {cfg["camera"]["crop"]}  (Zoom {3840/w:.3f}) → project.json')
