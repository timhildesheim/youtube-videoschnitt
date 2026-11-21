"""Shorts/Reels/TikToks (9:16) aus dem geschnittenen Video – im Arbeitsordner ausführen, nach Schritt 10 (Mix).

    python3 $SK/scripts/shorts.py                 # alle Einträge aus shorts.json
    python3 $SK/scripts/shorts.py anna-ring       # nur diese(n)
    python3 $SK/scripts/shorts.py --vorschau      # nur Kontrollbilder, kein Render

shorts.json (im Arbeitsordner, Zeiten = SCHNITTZEIT des fertigen Videos ohne Opener, also wie im Transkript-Export):
    [{"name": "anna-ring", "from": 312.4, "to": 361.0, "titel": "Warum Anna *nie* Schmuck trägt",
      "face_x": 0.52, "zoom": 1.0}]
  name    Dateiname (ohne Endung) · from/to 20–60 s, an Satzgrenzen (export_texts.py-Transkript)
  titel   Hook oben in den ersten Sekunden (ein Wort mit *…* betont), leer = kein Titel
  face_x  horizontale Gesichtsmitte im 16:9-Bild (0..1), Standard layout.face aus project.json
  zoom    > 1 schneidet enger (z. B. 1.15)

Bild: base.mp4 (geschnittenes 4K-Video ohne Einblendungen) → 9:16 um das Gesicht. Ton: mix_final.wav, sonst
voice_fx.wav. Untertitel: Wort für Wort aus dem Transkript, 1–3 Wörter je Einblendung, das gesprochene Wort in der
Akzentfarbe, Schrift aus dem Profil. Unten klein Kanalbild + Handle.
Ergebnis: <Videoordner>/Shorts/<name>.mp4 (1080×1920, 30 fps, −14 LUFS).
"""
import html as H, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import profil as PR

W = os.getcwd()
CFG = json.load(open('project.json'))
F = PR.get('marke.farben')
RGB = {k: PR.hex_rgb(v) for k, v in F.items()}
SANS = PR.get('marke.schriften.text') or 'Poppins'
FACE_X = (CFG.get('layout') or {}).get('face', [0.5, 0.4])[0]
args = [a for a in sys.argv[1:] if not a.startswith('--')]
ONLY_PREVIEW = '--vorschau' in sys.argv
OUTDIR = os.path.join('..', 'Shorts')
TARGET = PR.get('ton.ziel_lufs', -14)
run = lambda c, **k: subprocess.run(c, check=True, **k)

jobs = json.load(open('shorts.json'))
if args:
    jobs = [j for j in jobs if j['name'] in args]
assert jobs, 'shorts.json leer oder Name nicht gefunden'

# Wörter in Schnittzeit (wie export_texts.py)
tm = json.load(open('timemap.json'))


def cut_time(t):
    for s, e, c, *_ in tm:
        if t < s:
            return c
        if s <= t < e:
            return c + t - s
    return tm[-1][2] + tm[-1][1] - tm[-1][0]


WORDS = [{'text': x['text'].strip(), 'start': cut_time(x['start']), 'end': cut_time(x.get('end', x['start'] + 0.3))}
         for x in json.load(open('transcript/transcript.json')) if x['text'].strip()]


def chunks(ws, maxw=3, maxc=18):
    """1–3 Wörter je Einblendung; Umbruch nach Satzzeichen, Pausen oder zu langen Zeilen."""
    out, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        nxt = ws[i + 1] if i + 1 < len(ws) else None
        txt = ' '.join(x['text'] for x in cur)
        if (nxt is None or len(cur) >= maxw or len(txt) + len(nxt['text']) > maxc
                or w['text'].endswith(('.', ',', '?', '!', ':', ';')) or nxt['start'] - w['start'] > 0.9):
            out.append(cur)
            cur = []
    return out


def rich(s):
    s = H.escape(s)
    return re.sub(r"\*(.+?)\*", r'<span style="color:var(--akzent)">\1</span>', s)


def build(job):
    name, t0, t1 = job['name'], float(job['from']), float(job['to'])
    dur = round(t1 - t0, 3)
    d = os.path.join(W, 'shorts', name)
    os.makedirs(d, exist_ok=True)
    # Assets kopieren (keine Symlinks – HyperFrames liefert Ziele außerhalb des Ordners nicht aus)
    for a in PR.asset_files():
        dst = os.path.join(d, os.path.basename(a))
        if not os.path.exists(dst):
            shutil.copy2(os.path.realpath(a), dst)
    # Bild: 9:16-Ausschnitt um das Gesicht aus base.mp4 (Höhe voll, Breite = H·9/16 / zoom)
    fx = float(job.get('face_x', FACE_X))
    z = float(job.get('zoom', 1.0))
    crop = (f"crop=w='trunc(ih*9/16/{z}/2)*2':h='trunc(ih/{z}/2)*2':"
            f"x='max(0,min(iw-ow,{fx}*iw-ow/2))':y='max(0,min(ih-oh,(ih-oh)*0.3))',scale=1080:1920:flags=lanczos,fps=30")
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t0:.3f}', '-i', 'base.mp4', '-t', f'{dur:.3f}', '-an', '-vf', crop,
         *PR.h264('16M'), '-g', '15', '-pix_fmt', 'yuv420p', os.path.join(d, 'bg.mp4')])
    audio = 'mix_final.wav' if os.path.exists('mix_final.wav') else 'voice_fx.wav'
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t0:.3f}', '-i', audio, '-t', f'{dur:.3f}', '-af',
         f'afade=t=in:d=0.15,afade=t=out:st={max(0, dur - 0.4):.3f}:d=0.4', '-ar', '48000', '-ac', '2',
         os.path.join(d, 'audio.wav')])

    ws = [dict(w, start=w['start'] - t0, end=w['end'] - t0) for w in WORDS if t0 - 0.05 <= w['start'] < t1 - 0.05]
    cs = chunks(ws)
    lay, js = [], []
    for k, c in enumerate(cs):
        a = max(0.0, c[0]['start'])
        b = cs[k + 1][0]['start'] if k + 1 < len(cs) else dur
        b = min(b, c[-1]['start'] + 2.2)   # in langen Pausen nicht ewig stehen lassen
        spans = ''.join(f'<span id="w{k}_{j}" class="cw">{H.escape(w["text"])}</span> ' for j, w in enumerate(c))
        lay.append(f'<div id="c{k}" class="cap">{spans.strip()}</div>')
        js.append(f"tl.fromTo('#c{k}',{{opacity:0,y:18,scale:.94}},{{opacity:1,y:0,scale:1,duration:.16,ease:'back.out(2)'}},{a:.3f});")
        js.append(f"tl.set('#c{k}',{{opacity:0}},{b:.3f});")
        for j, w in enumerate(c):
            js.append(f"tl.set('#w{k}_{j}',{{color:'{F['akzent']}'}},{max(a, w['start']):.3f});")
            js.append(f"tl.set('#w{k}_{j}',{{color:'{F['papier']}'}},{min(b, (c[j + 1]['start'] if j + 1 < len(c) else b)):.3f});")

    titel = job.get('titel') or ''
    if titel:
        lay.append(f'<div id="ti" class="ti">{rich(titel)}</div>')
        js.append("tl.fromTo('#ti',{opacity:0,y:-20,filter:'blur(8px)'},{opacity:1,y:0,filter:'blur(0px)',duration:.6,ease:'power3.out'},0.1);")
        js.append(f"tl.to('#ti',{{opacity:0,y:-12,duration:.5,ease:'power2.in'}},{min(4.5, dur - 0.6):.3f});")
    av = PR.pfile(PR.get('kanal.avatar'))
    avh = f'<img src="{os.path.basename(av)}" style="width:64px;height:64px;border-radius:50%;object-fit:cover">' if av else ''
    lay.append(f'<div class="brand">{avh}<div><div style="font-weight:600;font-size:30px">{H.escape(PR.get("kanal.name") or "")}</div>'
               f'<div style="opacity:.7;font-size:24px">{H.escape(PR.get("kanal.handle") or "")}</div></div></div>')

    page = f'''<!doctype html>
<html lang="{PR.get('sprache', 'de')}"><head><meta charset="utf-8"><meta name="viewport" content="width=1080, height=1920">
<style>{PR.fonts_css()}
:root{{--akzent:{F['akzent']};--papier:{F['papier']};--basis:{F['basis']}}}
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#000;font-family:'{SANS}',system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden}}
video{{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}}
.grad{{position:absolute;left:0;right:0;bottom:0;height:900px;background:linear-gradient(to bottom,rgba({RGB['basis']},0),rgba({RGB['basis']},.55))}}
.gtop{{position:absolute;left:0;right:0;top:0;height:520px;background:linear-gradient(to top,rgba({RGB['basis']},0),rgba({RGB['basis']},.5))}}
.cap{{position:absolute;left:70px;right:70px;top:1230px;text-align:center;opacity:0;color:var(--papier);font-weight:700;font-size:92px;line-height:1.05;letter-spacing:-.03em;
text-shadow:0 2px 3px rgba(0,0,0,.35),0 6px 34px rgba(0,0,0,.55)}}
.ti{{position:absolute;left:80px;right:80px;top:230px;text-align:center;opacity:0;color:var(--papier);font-weight:700;font-size:70px;line-height:1.08;letter-spacing:-.035em;text-wrap:balance;
text-shadow:0 2px 3px rgba(0,0,0,.3),0 6px 30px rgba(0,0,0,.5)}}
.brand{{position:absolute;left:0;right:0;bottom:150px;display:flex;align-items:center;justify-content:center;gap:18px;color:var(--papier);text-shadow:0 2px 14px rgba(0,0,0,.5)}}
</style><script src="gsap.min.js"></script></head>
<body><div id="root" data-composition-id="{name}" data-start="0" data-duration="{dur}" data-fps="30" data-width="1080" data-height="1920">
<video id="bgv" src="bg.mp4" muted playsinline data-start="0" data-media-start="0" data-duration="{dur}" data-track-index="0"></video>
<div class="gtop"></div><div class="grad"></div>
{chr(10).join(lay)}
</div>
<script>
const tl=gsap.timeline({{paused:true}});
{chr(10).join(js)}
tl.set({{}},{{}},{dur});
window.__timelines["{name}"]=tl;
</script></body></html>'''
    open(os.path.join(d, 'index.html'), 'w').write(page)
    return d, dur, cs


os.makedirs(OUTDIR, exist_ok=True)
for job in jobs:
    d, dur, cs = build(job)
    print(f"• {job['name']}: {dur:.1f} s, {len(cs)} Untertitel-Einblendungen")
    if dur > 60:
        print('  ⚠ länger als 60 s – YouTube Shorts erlaubt bis 3 min, Reels/TikTok-Reichweite ist unter 60 s meist besser')
    if ONLY_PREVIEW:
        ts = ','.join(f'{x:.1f}' for x in (1.0, dur * 0.35, dur * 0.7))
        subprocess.run(['npx', 'hyperframes', 'snapshot', '.', '--at', ts], cwd=d, capture_output=True)
        continue
    tmp = os.path.join(d, 'render.mp4')
    run(['npx', 'hyperframes', 'render', '.', '-o', tmp, '--quiet'], cwd=d)
    out = os.path.join(OUTDIR, f"{job['name']}.mp4")
    run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-i', os.path.join(d, 'audio.wav'), '-map', '0:v', '-map', '1:a',
         '-c:v', 'copy', '-af', f'loudnorm=I={TARGET}:TP=-1.5:LRA=11', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000',
         '-shortest', '-movflags', '+faststart', out])
    os.remove(tmp)
    print(f'  → {out}')
