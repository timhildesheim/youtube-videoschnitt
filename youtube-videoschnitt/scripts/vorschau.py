"""Vorschau des Designsystems: rendert typische Einblendungen in den Farben/Schriften des Profils als Standbilder.

    python3 $SK/scripts/vorschau.py [hintergrund.jpg|.png|.mp4]

Hintergrund: am besten ein Standbild aus einer echten Aufnahme (Bildschirm oder Kamera). Ohne Angabe wird ein
neutraler Verlauf erzeugt. Ergebnis: <Profil>/vorschau/vorschau.jpg (Kontaktbogen, 3×3) – der Person zeigen und
Farben/Schriften so lange anpassen (profil.json → setup_profil.py → vorschau.py), bis es gefällt.
"""
import glob, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import profil as PR

if not PR.EXISTS:
    sys.exit('Kein Profil – erst das Einrichtungsinterview führen.')
W = os.path.join(PR.PDIR, 'vorschau')
shutil.rmtree(W, ignore_errors=True)
os.makedirs(os.path.join(W, 'assets'))
DUR = 40.0
bg = sys.argv[1] if len(sys.argv) > 1 else None
run = lambda c, **k: subprocess.run(c, check=True, **k)

if bg and bg.lower().endswith(('.mp4', '.mov', '.mkv')):
    run(['ffmpeg', '-v', 'error', '-y', '-stream_loop', '-1', '-i', bg, '-t', str(DUR), '-an', '-vf', 'scale=1920:1080,fps=30',
         *PR.h264('20M'), '-g', '15', '-pix_fmt', 'yuv420p', f'{W}/base.mp4'])
elif bg:
    run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', bg, '-t', str(DUR), '-vf', 'scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30',
         *PR.h264('20M'), '-g', '15', '-pix_fmt', 'yuv420p', f'{W}/base.mp4'])
else:
    c1, c2 = PR.get('marke.farben.basis2'), PR.get('marke.farben.marke1')
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'gradients=s=1920x1080:c0={c1}:c1={c2}:x0=0:y0=0:x1=1920:y1=1080:d={DUR}:r=30',
         '-t', str(DUR), *PR.h264('20M'), '-g', '15', '-pix_fmt', 'yuv420p', f'{W}/base.mp4'])

# CTA-Screenshot: echte Seite, wenn möglich – sonst Platzhalter
cta_url = PR.get('cta.screenshot_url') or PR.get('cta.url')
ok = False
if PR.get('cta.aktiv') and cta_url:
    ok = subprocess.run(['node', os.path.join(HERE, 'shots.mjs'), cta_url, 'cta'], cwd=W, capture_output=True).returncode == 0
if not ok:
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f"color=c={PR.get('marke.farben.sand')}:s=1440x900", '-frames:v', '1',
         f'{W}/assets/cta.jpg'])

json.dump({'source': 'vorschau', 'fps': 30, 'duration': DUR, 'layout': {'type': 'fullscreen', 'face': [0.5, 0.4], 'cam': None,
           'screen': {'x': 0, 'y': 0, 'w': 1920, 'h': 1080}}, 'subscribe_pos': {'left': 80, 'top': 860}},
          open(f'{W}/project.json', 'w'))
json.dump([[0, DUR, 0, 'SC']], open(f'{W}/timemap.json', 'w'))
name = PR.get('person.name') or 'Vorname Nachname'
first, _, last = name.partition(' ')
open(f'{W}/story.py', 'w').write(f'''import sys
sys.path.insert(0, {HERE!r})
from lib import *
comps = COMPS
c = comp('v1', 0, 20)
c.tile('t1', 0.3, 4.6, {{'left': 110, 'top': 150}}, 'Tipp', 'Erst *recherchieren*, dann bauen', sub='Kurze Unterzeile mit einem Detail', w=640)
c.chips('c1', 0.3, 4.6, {{'left': 1240, 'top': 170}}, '', [(0.4, 'Tool *eins*'), (0.6, 'Tool zwei'), (0.8, 'Tool drei')], w=560)
c.tag('g1', 0.3, 4.6, {{'left': 760, 'top': 880}}, 'Ergebnis *steht*')
c.listcard('l1', 5.0, 9.6, {{'left': 110, 'top': 170}}, 'In diesem Video', None, [(5.1, 'Schritt *eins*'), (5.3, 'Schritt zwei'), (5.5, 'Schritt drei')], w=600, num=True)
c.quote('q1', 5.0, 9.6, {{'left': 900, 'top': 600}}, '', 'Ein Satz, der hängen *bleiben* soll.', w=880)
c.chapter('k1', 10.0, 14.6, 2, 'Kapitel*titel*', total=4)
c.learning('n1', 15.0, 19.6, 1, 'Das wichtigste *Learning* in einem Satz')
c = comp('v2', 20, 40)
c.compare('m1', 20.3, 24.6, {{'left': 110, 'top': 170}}, '', 'Aufwand *vorher* und nachher', [(20.4, 'Ohne System', 100, 'var(--papier)', 'viel'), (20.6, 'Mit System', 22, 'var(--marke3)', 'wenig')], w=680)
c.tile('nm', 20.3, 24.6, {{'left': 110, 'top': 820}}, {(PR.get('person.zusatz') or '')!r}, {(first + (' *' + last + '*' if last else '')) !r}, w=600, size=52)
c.subscribe('a1', 25.0)
c.community('cm', 30.0, 34.6, [(30.2, 'Vorteil *eins*'), (30.4, 'Vorteil zwei'), (30.6, 'Vorteil drei')], pill_at=30.8)
c.before_after('ba', [(35.2, 0), (36.4, 1)])
endcard()
''')
run([sys.executable, os.path.join(HERE, 'build.py')], cwd=W, stdout=subprocess.DEVNULL)
shots = {'v1': [2.4, 7.6, 12.4, 17.6], 'v2': [2.8, 8.4, 13.2, 16.6], 'end': [3.0]}
k = 0
for sid, ts in shots.items():
    d = f'{W}/segs/{sid}'
    shutil.rmtree(f'{d}/.hyperframes/artifacts/snapshots', ignore_errors=True)
    subprocess.run(['npx', 'hyperframes', 'snapshot', '.', '--at', ','.join(map(str, ts))], cwd=d, capture_output=True)
    # neuere HyperFrames-Versionen legen die Bilder unter .hyperframes/artifacts/snapshots/<uuid>/ ab
    shots_ = sorted(glob.glob(f'{d}/snapshots/frame-*.png')) or sorted(glob.glob(f'{d}/.hyperframes/artifacts/snapshots/*/frame-*.png'))
    for f in shots_[:len(ts)]:
        run(['ffmpeg', '-v', 'error', '-y', '-i', f, '-vf', 'scale=960:-1', f'{W}/p_{k:02d}.jpg'])
        k += 1
open(f'{W}/_l.txt', 'w').write(''.join(f"file '{f}'\n" for f in sorted(glob.glob(f'{W}/p_*.jpg'))))
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{W}/_l.txt', '-vf', 'tile=3x3:padding=8:color=black',
     '-frames:v', '1', '-q:v', '2', f'{W}/vorschau.jpg'])
print(f'{k} Bilder → {W}/vorschau.jpg')
