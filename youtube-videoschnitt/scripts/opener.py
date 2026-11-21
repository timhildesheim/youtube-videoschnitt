"""Cartoon-/Erklär-Opener (1–2 min) aus Szenenbildern/-clips, Sprecher und Musik – references/opener.md.

    ~/.cache/youtube-videoschnitt/mgenv/bin/python $SK/scripts/opener.py <Videoordner>/opener [--vorschau]

Erwartet <ordner>/opener.json:
{
  "voiceover": "voiceover.wav",          optional – Sprechertext als eine Datei (eigene Stimme oder TTS)
  "musik": "musik.mp3", "musik_db": -20, optional – wird unter dem Sprecher automatisch abgesenkt
  "uebergang": "wisch",                  wisch (Akzent-Wisch wie im Intro) | blende | schnitt
  "szenen": [
    {"bild": "s01.png", "dauer": 6.0, "bewegung": "zoom-in", "text": "Das ist *Anna*.", "text_pos": "unten-links"},
    {"video": "s02.mp4", "dauer": 5.0, "text": "Seit 2009 lötet sie in *Plagwitz*."},
    {"bild": "s03.png", "dauer": 4.0, "bewegung": "parallax", "vordergrund": "s03_fg.png"}
  ]
}
bewegung: zoom-in | zoom-out | pan-links | pan-rechts | parallax (braucht "vordergrund", PNG mit Transparenz) | ruhig
text: kurze Comic-Zeile (*Betonung* in Akzentfarbe), Wörter ploppen nacheinander rein. text_pos: unten-links |
unten-mitte | oben-links. "text_ab": Sekunde in der Szene (Standard 0.4).
Ergebnis: <ordner>/../opener.mp4 (1920×1080, 30 fps, −14 LUFS) – assemble.py stellt es automatisch voran.
"""
import html as H, json, os, re, shutil, subprocess, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import profil as PR

D = os.path.abspath(sys.argv[1])
PREVIEW = '--vorschau' in sys.argv
J = json.load(open(os.path.join(D, 'opener.json')))
F = PR.get('marke.farben')
RGB = {k: PR.hex_rgb(v) for k, v in F.items()}
SANS = PR.get('marke.schriften.text') or 'Poppins'
TARGET = PR.get('ton.ziel_lufs', -14)
TR = J.get('uebergang', 'wisch')
run = lambda c, **k: subprocess.run(c, check=True, **k)
B = os.path.join(D, '_build')
os.makedirs(B, exist_ok=True)

q = lambda t: round(round(t * 30) / 30, 4)


def rich_words(s):
    out = []
    for part in re.split(r'(\*[^*]+\*)', s):
        if not part:
            continue
        acc = part.startswith('*') and part.endswith('*')
        for w in (part[1:-1] if acc else part).split():
            if out and not re.search(r'\w', w):   # reine Satzzeichen ohne Leerzeichen ans vorige Wort („Plagwitz.“)
                out[-1] += f'<span class="ow">{H.escape(w)}</span>'
                continue
            style = ' style="color:var(--akzent)"' if acc else ''
            out.append(f'<span class="ow"{style}>{H.escape(w)}</span>')
    return ' '.join(out)


POS = {'unten-links': 'left:110px;bottom:120px;text-align:left', 'unten-mitte': 'left:160px;right:160px;bottom:120px;text-align:center',
       'oben-links': 'left:110px;top:110px;text-align:left'}
MOVES = {'zoom-in': ('{scale:1.04}', '{scale:1.16}'), 'zoom-out': ('{scale:1.16}', '{scale:1.04}'),
         'pan-links': ('{scale:1.12,x:60}', '{scale:1.12,x:-60}'), 'pan-rechts': ('{scale:1.12,x:-60}', '{scale:1.12,x:60}'),
         'parallax': ('{scale:1.06,x:20}', '{scale:1.1,x:-20}'), 'ruhig': ('{scale:1.05}', '{scale:1.07}')}

# Assets kopieren (keine Symlinks: HyperFrames liefert Ziele außerhalb des Ordners nicht aus)
for a in PR.asset_files():
    shutil.copy2(os.path.realpath(a), os.path.join(B, os.path.basename(a)))
lay, js, sfx, t = [], [], [], 0.0
for i, s in enumerate(J['szenen']):
    dur = q(float(s['dauer']))
    sid = f's{i}'
    src = s.get('bild') or s.get('video')
    shutil.copy2(os.path.join(D, src), os.path.join(B, os.path.basename(src)))
    mv = MOVES.get(s.get('bewegung', 'zoom-in'), MOVES['zoom-in'])
    if s.get('video'):
        media = (f'<video id="{sid}-m" src="{os.path.basename(src)}" muted playsinline data-start="{t}" data-media-start="0" '
                 f'data-duration="{dur}" data-track-index="{i}" style="position:absolute;inset:0;width:1920px;height:1080px;object-fit:cover"></video>')
    else:
        media = f'<img id="{sid}-m" src="{os.path.basename(src)}" style="position:absolute;inset:0;width:1920px;height:1080px;object-fit:cover">'
    fg = ''
    if s.get('vordergrund'):
        shutil.copy2(os.path.join(D, s['vordergrund']), os.path.join(B, os.path.basename(s['vordergrund'])))
        fg = f'<img id="{sid}-fg" src="{os.path.basename(s["vordergrund"])}" style="position:absolute;inset:0;width:1920px;height:1080px;object-fit:cover">'
    txt = ''
    if s.get('text'):
        txt = (f'<div id="{sid}-t" class="ot" style="{POS.get(s.get("text_pos", "unten-links"), POS["unten-links"])}">'
               f'<span class="pl"><span class="pi">{rich_words(s["text"])}</span></span></div>')
    lay.append(f'<div id="{sid}" class="sz" style="opacity:0"><div id="{sid}-k" class="kb">{media}{fg}</div>{txt}</div>')
    js.append(f"tl.set('#{sid}',{{opacity:1}},{t});tl.set('#{sid}',{{opacity:0}},{q(t + dur)});")
    if TR == 'blende' and i:
        js.append(f"tl.fromTo('#{sid}',{{opacity:0}},{{opacity:1,duration:.5,ease:'power1.inOut'}},{t});")
    js.append(f"tl.fromTo('#{sid}-k',{mv[0]},{{...{mv[1]},duration:{dur},ease:'none'}},{t});")
    if fg:
        js.append(f"tl.fromTo('#{sid}-fg',{{x:30}},{{x:-70,duration:{dur},ease:'none'}},{t});")
    if txt:
        ta = q(t + float(s.get('text_ab', 0.4)))
        js.append(f"tl.fromTo('#{sid}-t .pl',{{scaleX:0,opacity:1}},{{scaleX:1,duration:.35,ease:'power3.out'}},{q(ta - 0.15)});")
        js.append(f"tl.fromTo('#{sid}-t .ow',{{opacity:0,y:40,scale:.6,rotation:-4}},{{opacity:1,y:0,scale:1,rotation:0,duration:.45,ease:'back.out(2.4)',stagger:.07}},{ta});")
        sfx.append((ta, 'pop', 0.10))
    if TR == 'wisch' and i:   # Wisch über die Schnittkante: deckt bei t ab, gibt danach die neue Szene frei
        wid = f'w{i}'
        lay.append(f'<div id="{wid}" class="wp" style="opacity:0"></div>')
        js.append(f"tl.fromTo('#{wid}',{{x:-2700,opacity:1}},{{x:2300,duration:.6,ease:'power3.inOut'}},{q(t - 0.3)});tl.set('#{wid}',{{opacity:0}},{q(t + 0.35)});")
        sfx.append((t - 0.3, 'whoosh-short', 0.16))
    t = q(t + dur)
TOTAL = t
# Schluss: Akzent-Wisch, dann Basis – nahtloser Übergang ins Marken-Intro
lay.append('<div id="wend" class="wp" style="opacity:0"></div><div id="wend2" class="wp" style="opacity:0;background:var(--basis)"></div>')
js.append(f"tl.fromTo('#wend',{{x:-2700,opacity:1}},{{x:-200,duration:.55,ease:'power3.in'}},{q(TOTAL - 0.55)});")
js.append(f"tl.fromTo('#wend2',{{x:-2900,opacity:1}},{{x:-200,duration:.5,ease:'power3.in'}},{q(TOTAL - 0.45)});")
sfx.append((TOTAL - 0.6, 'whoosh', 0.18))

page = f'''<!doctype html>
<html lang="{PR.get('sprache', 'de')}"><head><meta charset="utf-8"><meta name="viewport" content="width=1920, height=1080">
<style>{PR.fonts_css()}
:root{{--akzent:{F['akzent']};--papier:{F['papier']};--basis:{F['basis']}}}
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:var(--basis);font-family:'{SANS}',system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
#root{{position:relative;width:1920px;height:1080px;overflow:hidden}}
.sz{{position:absolute;inset:0;overflow:hidden}}
.kb{{position:absolute;inset:0;transform-origin:50% 45%}}
.ot{{position:absolute;max-width:1400px;color:var(--papier);font-weight:700;font-size:74px;line-height:1.08;letter-spacing:-.035em}}
.pl{{display:inline-block;background:rgba({RGB['basis']},.92);padding:16px 34px 20px;transform:skewX(-7deg);transform-origin:0 100%;box-shadow:0 18px 50px rgba(0,0,0,.35);text-align:left}}
.pi{{display:inline-block;transform:skewX(7deg);text-wrap:balance}}
.ow{{display:inline-block}}
.wp{{position:absolute;left:0;top:-120px;width:2500px;height:1320px;background:var(--akzent);transform:skewX(-9deg)}}
</style><script src="gsap.min.js"></script></head>
<body><div id="root" data-composition-id="opener" data-start="0" data-duration="{TOTAL}" data-fps="30" data-width="1920" data-height="1080">
{chr(10).join(lay)}
</div>
<script>
const tl=gsap.timeline({{paused:true}});
{chr(10).join(js)}
tl.set({{}},{{}},{TOTAL});
window.__timelines["opener"]=tl;
</script></body></html>'''
open(os.path.join(B, 'index.html'), 'w').write(page)
print(f'Opener: {len(J["szenen"])} Szenen, {TOTAL:.1f} s')
if TOTAL > 150:
    print('⚠ länger als 2:30 – für den Einstieg eher 60–120 s anpeilen')

if PREVIEW:
    ts = [q(sum(float(x['dauer']) for x in J['szenen'][:k]) + float(s['dauer']) * 0.6) for k, s in enumerate(J['szenen'])]
    subprocess.run(['npx', 'hyperframes', 'snapshot', '.', '--at', ','.join(map(str, ts))], cwd=B)
    sys.exit(0)

# ───────── Ton: Sprecher + Musik (abgesenkt unter Sprache) + Sound-Effekte → −14 LUFS ─────────
SR = 48000
N = int(TOTAL * SR)


def load(p):
    tmp = os.path.join(B, '_a.wav')
    run(['ffmpeg', '-v', 'error', '-y', '-i', p, '-ar', str(SR), '-ac', '2', tmp])
    a, _ = sf.read(tmp, dtype='float32', always_2d=True)
    return a


mix = np.zeros((N, 2), np.float32)
vo = np.zeros((N, 2), np.float32)
if J.get('voiceover'):
    v = load(os.path.join(D, J['voiceover']))[:N]
    vo[:len(v)] = v
    if len(v) > N:
        print(f'⚠ Sprecher ({len(v)/SR:.1f} s) länger als die Szenen ({TOTAL:.1f} s) – Szenendauern anpassen')
mix += vo
if J.get('musik'):
    m = load(os.path.join(D, J['musik']))
    m = np.concatenate([m] * (N // len(m) + 1))[:N]
    m *= 10 ** (J.get('musik_db', -20) / 20) / (np.sqrt(np.mean(m ** 2)) + 1e-9)
    env = np.abs(vo.mean(1))
    k = int(0.3 * SR)
    env = np.convolve(env, np.ones(k) / k, mode='same')
    duck = 1 - 0.6 * np.clip(env / (np.percentile(env[env > 1e-4], 70) if (env > 1e-4).any() else 1), 0, 1)
    fade = np.ones(N, np.float32)
    fo = int(1.5 * SR)
    fade[-fo:] = np.linspace(1, 0, fo)
    mix += m * (duck * fade)[:, None]
for ts_, name, g in sfx:
    x = load(os.path.join(PR.SKILL, 'assets/sfx', f'{name}.mp3'))
    x *= 10 ** (-12 / 20) / (np.abs(x).max() + 1e-9)
    i0 = max(0, int(ts_ * SR))
    n = min(len(x), N - i0)
    if n > 0:
        mix[i0:i0 + n] += x[:n] * g * 1.6
sf.write(os.path.join(B, 'mix_pre.wav'), mix, SR, subtype='FLOAT')
# Pegel wie assemble.py: Gesamtlautheit messen, linear auf Ziel-LUFS anheben, Spitzen begrenzen (kein Kompressor)
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', os.path.join(B, 'mix_pre.wav'), '-af', 'ebur128=framelog=quiet', '-f', 'null', '-'],
                   capture_output=True, text=True)
I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r.stderr)[-1])
run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(B, 'mix_pre.wav'), '-af',
     f'volume={TARGET - I:.2f}dB,alimiter=limit=0.84:attack=1:release=60:level=false', '-ar', str(SR), os.path.join(B, 'mix.wav')])

run(['npx', 'hyperframes', 'render', '.', '-o', 'video.mp4', '--quiet'], cwd=B)
out = os.path.join(os.path.dirname(D), 'opener.mp4')
run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(B, 'video.mp4'), '-i', os.path.join(B, 'mix.wav'), '-map', '0:v', '-map', '1:a',
     '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k',
     '-shortest', '-movflags', '+faststart', out])
print(f'→ {out}')
