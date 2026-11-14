"""Schritt 7b: Kontrollbilder je Segment – ~1,6 s nach jedem Karteneinstieg – plus Kontaktbögen.

    python3 qa.py            # alle Segmente
    python3 qa.py s03 th1    # nur diese (nach Änderungen)

Ergebnis: qa/sheet_XX.jpg (4×5 Bilder). Jedes Blatt ansehen, bevor gerendert wird:
Lesbarkeit, Überdeckung der Kamera/des Gesichts, leere Kartenflächen, abgeschnittener Text.
"""
import glob, json, os, shutil, subprocess, sys

man = json.load(open('manifest.json'))
ids = sys.argv[1:]
os.makedirs('qa', exist_ok=True)
for f in glob.glob('qa/*.jpg'):
    os.remove(f)
k = 0
for m in man:
    if ids and m['id'] not in ids:
        continue
    ts = sorted(set(round(min(m['dur'] - 0.6, max(0.3, t - m['t0'] + 1.6)), 2) for t in m.get('cues', []) + [x[0] for x in m['sfx']])) or [round(m['dur'] / 2, 2)]
    keep = []
    for t in ts:
        if not keep or t - keep[-1] > 1.2:
            keep.append(t)
    d = f'segs/{m["id"]}'
    shutil.rmtree(f'{d}/snapshots', ignore_errors=True)
    shutil.rmtree(f'{d}/.hyperframes/artifacts/snapshots', ignore_errors=True)
    subprocess.run(['npx', 'hyperframes', 'snapshot', '.', '--at', ','.join(map(str, keep))], cwd=d, capture_output=True)
    # neuere HyperFrames-Versionen legen die Bilder unter .hyperframes/artifacts/snapshots/<uuid>/ ab (Okt. 2026)
    shots = sorted(glob.glob(f'{d}/snapshots/frame-*.png')) or sorted(glob.glob(f'{d}/.hyperframes/artifacts/snapshots/*/frame-*.png'))
    for f in shots[:len(keep)]:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f, '-vf', 'scale=640:-1', f'qa/{k:03d}_{m["id"]}.jpg'])
        k += 1
    print(m['id'], keep, flush=True)
n = 0
files = sorted(glob.glob('qa/[0-9]*.jpg'))
for i in range(0, len(files), 20):
    lst = 'qa/_list.txt'
    open(lst, 'w').write(''.join(f"file '{os.path.abspath(f)}'\n" for f in files[i:i + 20]))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-vf', 'tile=4x5', '-frames:v', '1', f'qa/sheet_{n:02d}.jpg'])
    n += 1
print(f'{k} Bilder → qa/sheet_00 … sheet_{n-1:02d}.jpg (Reihenfolge = Dateinamen in qa/)')
