"""Schritt 9: Hintergrundmusik lokal mit MusicGen komponieren.

Mit der MusicGen-Umgebung ausführen:
    ~/.cache/youtube-videoschnitt/mgenv/bin/python music.py intro=120 work=140 reveal=110 outro=130

Für jede Stimmung: zwei 30-s-Varianten erzeugen, die gleichmäßigere wählen, per Fortsetzung auf die
Ziellänge (Sekunden) verlängern, Aussetzer (> 1 s deutlich leiser als die Umgebung) automatisch mit
Überblendung herausschneiden. Ergebnis: music/<stimmung>_long.wav (32 kHz mono).
Eigene Stimmungen: im Profil (ton.musik_stimmungen) oder als 'name:prompt-text=sekunden' übergeben.
"""
import os, sys, time
import numpy as np, soundfile as sf, torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration

PROMPTS = {
    'intro': 'uplifting modern instrumental, warm plucked electric guitar, soft claps, light percussion, bright optimistic chords, feel-good youtube intro, 110 bpm, clean mix, no vocals',
    'work': 'chill lofi hip hop instrumental, soft rhodes electric piano chords, mellow bass, relaxed brushed drums, warm and focused, 88 bpm, no vocals',
    'reveal': 'calm cinematic ambient instrumental, airy warm pads, gentle felt piano melody, soft pulse, hopeful and elegant, 90 bpm, no vocals',
    'outro': 'upbeat warm deep house groove instrumental, smooth synth chords, soft kick, positive and confident, 118 bpm, no vocals',
    'tension': 'minimal modern electronic instrumental, pulsing synth bass, ticking percussion, curious and focused, 100 bpm, no vocals',
}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profil as PR
PROMPTS.update(PR.get('ton.musik_stimmungen') or {})   # eigene Stimmungen aus dem Profil
jobs = []
for arg in sys.argv[1:]:
    name, sec = arg.rsplit('=', 1)
    if ':' in name:
        name, prompt = name.split(':', 1)
        PROMPTS[name] = prompt
    jobs.append((name, float(sec)))
os.makedirs('music', exist_ok=True)
dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
proc = AutoProcessor.from_pretrained('facebook/musicgen-medium')
model = MusicgenForConditionalGeneration.from_pretrained('facebook/musicgen-medium').to(dev)
SR = model.config.audio_encoder.sampling_rate


def gen(prompt, seed, audio=None, new_sec=30):
    torch.manual_seed(seed)
    kw = dict(text=[prompt], padding=True, return_tensors='pt')
    if audio is not None:
        kw.update(audio=audio, sampling_rate=SR)
    inp = proc(**kw).to(dev)
    with torch.no_grad():
        out = model.generate(**inp, do_sample=True, guidance_scale=3.0, max_new_tokens=int(new_sec * 50) + 10)
    return out[0, 0].float().cpu().numpy()


def per_sec(a):
    return np.array([20 * np.log10(np.sqrt(np.mean(a[i * SR:(i + 1) * SR] ** 2)) + 1e-9) for i in range(len(a) // SR)])


def fix_dropouts(a):
    """Sekunden, die > 12 dB unter dem gleitenden Median liegen, mit 0,8-s-Blende herausschneiden."""
    for _ in range(6):
        p = per_sec(a)
        med = np.array([np.median(p[max(0, i - 6):i + 7]) for i in range(len(p))])
        bad = np.flatnonzero(p < med - 12)
        bad = bad[(bad > 1) & (bad < len(p) - 2)]
        if not len(bad):
            return a
        s, e = bad[0], bad[0]
        while e + 1 in bad:
            e += 1
        i, j = int((s - 0.3) * SR), int((e + 1.3) * SR)
        xf = int(0.8 * SR)
        r = np.linspace(0, 1, xf)
        a = np.concatenate([a[:i - xf], a[i - xf:i] * (1 - r) + a[j:j + xf] * r, a[j + xf:]])
        print(f'   Aussetzer bei {s}–{e}s entfernt')
    return a


for name, target in jobs:
    out = f'music/{name}_long.wav'
    if os.path.exists(out):
        print('vorhanden', out)
        continue
    t = time.time()
    cands = [gen(PROMPTS[name], s) for s in (1, 2)]
    # gleichmäßigste Variante (kleinste Pegelstreuung, keine Stille) nehmen; letzte 2 s abschneiden (Ausklang)
    score = [np.std(per_sec(c)[:-3]) + 10 * (per_sec(c)[:-3].min() < -40) for c in cands]
    a = cands[int(np.argmin(score))][:-2 * SR].astype(np.float32)
    seed = 7
    while len(a) / SR < target + 12:   # Reserve fürs Herausschneiden
        ctx = a[-10 * SR:]
        o = gen(PROMPTS[name], seed, audio=ctx, new_sec=20)
        seed += 1
        xf = int(0.25 * SR)
        r = np.linspace(0, 1, xf)
        a = np.concatenate([a[:-xf], a[-xf:] * (1 - r) + o[len(ctx) - xf:len(ctx)] * r, o[len(ctx):]])
    a = fix_dropouts(a)
    sf.write(out, a, SR)
    print(f'{name}: {len(a)/SR:.0f}s in {time.time()-t:.0f}s → {out}', flush=True)
