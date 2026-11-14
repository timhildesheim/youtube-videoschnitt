"""Schritt 1: Video untersuchen, Ton extrahieren, transkribieren, Übersichtsbilder erzeugen.

Aufruf (im Arbeitsordner <Videoordner>/<profil.ablage.arbeitsordner>/):
    python3 prepare.py "../<Hauptvideo>.mp4" [--lang de]   (Standard: profil.sprache)

Legt an: project.json (Grundgerüst), audio16k.wav, source_audio.wav, transcript/transcript.json,
transcript/lines.txt (Sätze mit Zeitmarken), frames/contact_XX.jpg (alle 20 s ein Bild),
frames/scenes.txt (Stellen, an denen sich das Bildlayout stark ändert).
"""
import json, os, re, subprocess, sys
import numpy as np

src = os.path.abspath(sys.argv[1])
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profil as _PR
lang = sys.argv[sys.argv.index('--lang') + 1] if '--lang' in sys.argv else _PR.get('sprache', 'de')
W = os.getcwd()
os.makedirs('frames', exist_ok=True)
os.makedirs('transcript', exist_ok=True)


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


# ── Metadaten ──
p = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate',
                               '-show_entries', 'format=duration', '-of', 'json', src], capture_output=True, text=True).stdout)
v = [s for s in p['streams'] if s['codec_type'] == 'video'][0]
num, den = map(int, v['r_frame_rate'].split('/'))
fps = round(num / den, 3)
dur = float(p['format']['duration'])
print(f'Video: {v["width"]}×{v["height"]} @ {fps} fps, {dur/60:.1f} min')
if v['width'] < 3840:
    print('⚠ Quelle ist nicht 4K – Ausgabe wird trotzdem in 3840×2160 gerendert (hochskaliert).')

if not os.path.exists('project.json'):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import profil as PR
    setups = PR.get('aufnahme.setups') or []
    lay = setups[0]['layout'] if setups else {'type': 'TODO: circle-cam | split | fullscreen', 'face': [0.5, 0.4],
                                               'cam': None, 'screen': None}
    cfg = {
        'source': src, 'fps': round(fps), 'duration': dur, 'language': lang,
        'layout': lay,
        '_layout': 'Vorbelegt mit dem ersten Setup aus dem Profil – immer am Video prüfen (references/layouts.md).',
        'talking_head_ranges': [], 'demo_ranges': [], 'manual_remove': [],
        'pause_keep': PR.get('schnitt.pause_keep'),
        'music': [], 'subscribe_pos': {'left': 80, 'top': 860},
    }
    cam_hint = PR.get('aufnahme.kamera_spur') or {}
    if cam_hint.get('crop'):
        cfg['camera'] = {'crop': cam_hint['crop']}
    json.dump(cfg, open('project.json', 'w'), indent=1, ensure_ascii=False)

# ── Ton ──
if not os.path.exists('audio16k.wav'):
    run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '1', '-ar', '16000', 'audio16k.wav'])
if not os.path.exists('source_audio.wav'):
    run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '2', '-ar', '48000', '-c:a', 'pcm_s16le', 'source_audio.wav'])

# ── Transkript (lokales Whisper large-v3/turbo) ──
if not os.path.exists('transcript/transcript.json'):
    print('Transkribiere … (≈ 3–6 min pro 30 min Video)')
    run(['npx', 'hyperframes', 'transcribe', 'audio16k.wav', '-d', 'transcript', '--engine', 'whisper',
         '--model', 'large-v3', '--language', lang, '--json', '--timeout', '7200000'], stdout=subprocess.DEVNULL)
w = json.load(open('transcript/transcript.json'))
out, cur, st = [], [], None
for i, x in enumerate(w):
    st = x['start'] if st is None else st
    cur.append(x['text'])
    nxt = w[i + 1]['start'] if i + 1 < len(w) else None
    if x['text'].rstrip().endswith(('.', '?', '!')) or nxt is None or nxt - x['end'] > 0.8 or len(cur) > 30:
        out.append(f"[{st:7.2f} | {int(st//60):02d}:{st%60:05.2f}] {' '.join(cur)}")
        cur, st = [], None
open('transcript/lines.txt', 'w').write('\n'.join(out))
print(f'Transkript: {len(w)} Wörter, {len(out)} Zeilen → transcript/lines.txt')

# ── Übersichtsbilder (alle 20 s, 6×4 pro Blatt) ──
if not os.path.exists('frames/contact_01.jpg'):
    run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', 'fps=1/20,scale=480:-1,tile=6x4', 'frames/contact_%02d.jpg'])

# ── Layout-Wechsel finden: Keyframes als 32×18-Signatur, große, anhaltende Sprünge melden ──
raw = subprocess.run(['ffmpeg', '-v', 'info', '-skip_frame', 'nokey', '-i', src, '-an', '-fps_mode', 'passthrough',
                      '-vf', 'scale=32:18,showinfo', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
ts = [float(m) for m in re.findall(rb'pts_time:([\d.]+)', raw.stderr)]
a = np.frombuffer(raw.stdout, np.uint8)
n = min(len(ts), len(a) // (32 * 18 * 3))
a = a[:n * 32 * 18 * 3].reshape(n, 18, 32, 3).astype(float)
sig = a.reshape(n, -1)
lines = []
for i in range(1, n - 1):
    d_prev = np.abs(sig[i] - sig[i - 1]).mean()
    d_next = np.abs(sig[i + 1] - sig[i]).mean()
    if d_prev > 28 and d_next < d_prev * 0.6:
        lines.append(f'{ts[i]:8.1f}s  Δ={d_prev:5.1f}')
open('frames/scenes.txt', 'w').write('\n'.join(lines))
print(f'{len(lines)} mögliche Layout-Wechsel → frames/scenes.txt (mit Einzelbildern prüfen)')
