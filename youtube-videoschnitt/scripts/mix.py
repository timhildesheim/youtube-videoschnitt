"""Schritt 10: Ton mischen – Stimme im Original, Musik nur in passenden Szenen (mit Ducking), Sound-Effekte.

Mit der MusicGen-Umgebung ausführen (braucht soundfile/scipy):
    ~/.cache/youtube-videoschnitt/mgenv/bin/python mix.py

project.json → "music": Liste von Fenstern in QUELLZEIT, z. B.
  {"track": "intro", "from": 0, "to": 128.5, "offset": 0, "speech_db": -21, "gap_db": -15}
  "to": "end" = bis zum Ende inkl. Endkarte. offset = Startpunkt im Musikstück (s).
  speech_db = Musikpegel unter Sprache, gap_db = in Sprechpausen (relativ zu -20 dBFS RMS).
Schreibt voice_fx.wav, mix_pre.wav und die Stems stem_voice.wav / stem_music.wav.
"""
import json, os, subprocess, sys
import numpy as np, soundfile as sf

W = os.getcwd()
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ['YT_WORK'] = W
sys.path.insert(0, os.path.join(SKILL, 'scripts'))
from lib import S, OUT_DUR, CFG
import profil as PR

SR = 48000
END_EXTRA = CFG.get('end_card_seconds', 5.0)
TOTAL = OUT_DUR + END_EXTRA
N = int(round(TOTAL * SR))

# Stimme: Standard ORIGINAL ('anull'). Eine Kette kommt nur aus dem Profil (ton.stimme_fx) oder für ein einzelnes
# Video aus project.json → "voice_fx". Erprobte Varianten und Messwerte stehen in references/audio.md.
VOICE_FX = CFG.get('voice_fx') or PR.get('ton.stimme_fx') or 'anull'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'voice_cut.wav', '-af', VOICE_FX, '-ar', str(SR), '-ac', '2',
                '-c:a', 'pcm_f32le', 'voice_fx.wav'], check=True)


def load(path):
    if sf.info(path).samplerate != SR or not path.endswith('.wav'):
        tmp = os.path.join(W, 'music', '_tmp_' + os.path.basename(path) + '.wav')
        os.makedirs(os.path.dirname(tmp), exist_ok=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-ar', str(SR), '-ac', '2', tmp], check=True)
        path = tmp
    a, _ = sf.read(path, dtype='float32', always_2d=True)
    return np.repeat(a, 2, 1) if a.shape[1] == 1 else a


db = lambda x: 10 ** (x / 20)
voice = load('voice_fx.wav')
mix_v = np.zeros((N, 2), np.float32)
mix_v[:min(N, len(voice))] = voice[:N]

# Sprach-Hüllkurve fürs Ducking (Attack 40 ms, Release 600 ms)
mono = mix_v.mean(1)
hop = 480
rms = np.sqrt(np.add.reduceat(mono ** 2, np.arange(0, N, hop)) / hop + 1e-12)
lvl = 20 * np.log10(rms)
act = (lvl > np.percentile(lvl[lvl > -70], 60) - 14).astype(np.float32)
env = np.zeros_like(act)
aa, ar, e = np.exp(-1 / 4), np.exp(-1 / 60), 0.0
for i, x in enumerate(act):
    e = aa * e + (1 - aa) * x if x > e else ar * e + (1 - ar) * x
    env[i] = e
duck = np.repeat(env, hop)[:N]

music = np.zeros((N, 2), np.float32)
cache = {}
for win in (CFG.get('music', []) if PR.get('ton.musik', True) else []):
    name = win['track']
    # "file": eigene Musikdatei (z. B. Intro-Jingle) – absolut, im Profilordner oder im Arbeitsordner.
    # Track "jingle" ohne file nimmt ton.intro_jingle aus dem Profil. Sonst music/<track>_long.wav (MusicGen).
    src = win.get('file') or (PR.get('ton.intro_jingle') if name == 'jingle' else None)
    if name not in cache:
        if src:
            src = os.path.expanduser(src)
            path = src if os.path.isabs(src) else (PR.pfile(src) or os.path.join(W, src))
        else:
            path = os.path.join(W, 'music', f'{name}_long.wav')
        t = load(path)
        cache[name] = t * (db(-20) / np.sqrt(np.mean(t ** 2)))
    tr = cache[name]
    t0 = S(win['from'])
    t1 = TOTAL if win['to'] == 'end' else S(win['to']) + win.get('tail', 2.5)
    i0, i1 = int(t0 * SR), min(N, int(t1 * SR))
    L = i1 - i0
    off = int(win.get('offset', 0) * SR)
    seg = tr[off:off + L]
    if len(seg) < L and not win.get('loop', not src):   # Jingle: nicht loopen, danach Stille
        seg = np.concatenate([seg, np.zeros((L - len(seg), 2), np.float32)])
    if len(seg) < L:
        print(f'⚠ Musik "{name}" zu kurz für Fenster {win["from"]}–{win["to"]} → wird geloopt; besser music.py mit mehr Sekunden')
        seg = np.concatenate([tr] * (L // len(tr) + 2))[off:off + L]
    fi, fo = int(win.get('fade_in', 1.2) * SR), int(win.get('fade_out', 4.0 if win['to'] == 'end' else 3.0) * SR)
    ramp = np.ones(L, np.float32)
    fi, fo = min(fi, L), min(fo, L)
    if fi > 0:
        ramp[:fi] = np.linspace(0, 1, fi) ** 2
    if fo > 0:
        ramp[-fo:] = np.linspace(1, 0, fo) ** 1.5
    d = duck[i0:i1]
    gain = db(win.get('gap_db', -16)) * (1 - d) + db(win.get('speech_db', -23)) * d
    music[i0:i1] += seg * (ramp * gain)[:, None]

sfx = np.zeros((N, 2), np.float32)
SFXDIR = os.path.join(SKILL, 'assets/sfx')
sc = {}
SFX_GAIN = PR.get('ton.sfx_pegel', 1.0) if PR.get('ton.sfx', True) else 0.0
for m in (json.load(open('manifest.json')) if SFX_GAIN > 0 else []):
    for t, name, g in m['sfx']:
        if name not in sc:
            x = load(os.path.join(SFXDIR, f'{name}.mp3'))
            sc[name] = x * (db(-12) / (np.abs(x).max() + 1e-9))
        x = sc[name]
        i0 = max(0, int(t * SR) - (int(0.12 * SR) if name.startswith('whoosh') else 0))
        n = min(len(x), N - i0)
        if n > 0:
            sfx[i0:i0 + n] += x[:n] * g * 1.6 * SFX_GAIN

sf.write('mix_pre.wav', mix_v + music + sfx, SR, subtype='FLOAT')
sf.write('stem_voice.wav', mix_v, SR, subtype='FLOAT')
sf.write('stem_music.wav', music, SR, subtype='FLOAT')
print(f'mix_pre.wav: {TOTAL/60:.2f} min · {len(CFG.get("music", []))} Musikfenster')
