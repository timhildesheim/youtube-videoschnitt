"""Erzeugt alle Sound-Effekte des Skills synthetisch (keine Samples, keine fremden Aufnahmen).

Aufruf:  python3 werkzeuge/make_sfx.py [Zielordner]
Standard-Ziel: youtube-videoschnitt/assets/sfx/. Braucht numpy, scipy und ffmpeg.
Fester Zufallsstartwert, damit jeder Lauf dieselben Dateien liefert.
"""
import os
import subprocess
import sys
import tempfile

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
RNG = np.random.default_rng(20261114)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'youtube-videoschnitt', 'assets', 'sfx')


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def noise(n):
    return RNG.standard_normal(n)


def env_adsr(n, a, d, peak_at=None, curve=2.0):
    """Hüllkurve: Anstieg über a Sekunden, danach exponentieller Abfall mit Zeitkonstante d."""
    t = np.arange(n) / SR
    att = np.clip(t / max(a, 1e-4), 0, 1) ** curve
    dec = np.exp(-np.clip(t - a, 0, None) / d)
    return att * dec


def bandpass_sweep(x, f0, f1, q=2.0, steps=64, shape=None):
    """Rauschen durch einen Bandpass schicken, dessen Mitte von f0 nach f1 wandert (blockweise)."""
    n = len(x)
    out = np.zeros(n)
    edges = np.linspace(0, n, steps + 1).astype(int)
    win_len = (edges[1] - edges[0]) * 2
    for i in range(steps):
        a, b = edges[i], edges[i + 1]
        pos = (i + 0.5) / steps
        if shape is not None:
            pos = shape(pos)
        fc = f0 * (f1 / f0) ** pos if f0 > 0 and f1 > 0 else f0 + (f1 - f0) * pos
        bw = fc / q
        lo, hi = max(20, fc - bw / 2), min(SR / 2 - 100, fc + bw / 2)
        sos = signal.butter(2, [lo, hi], btype='band', fs=SR, output='sos')
        s0, s1 = max(0, a - win_len // 4), min(n, b + win_len // 4)
        y = signal.sosfilt(sos, x[s0:s1])
        w = np.hanning(s1 - s0)
        out[s0:s1] += y * w
    return out


def lowpass(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, fs=SR, output='sos'), x)


def highpass(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, btype='high', fs=SR, output='sos'), x)


def reverb(x, size=0.6, mix=0.25, damp=6000):
    """Einfacher Hall: Faltung mit abklingendem, gefiltertem Rauschen. Gibt Stereo zurück."""
    n = int(size * SR)
    t = np.arange(n) / SR
    irs = []
    for _ in range(2):
        ir = lowpass(noise(n), damp) * np.exp(-t / (size / 5))
        ir[: int(0.008 * SR)] = 0
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    pad = np.concatenate([x, np.zeros(n)])
    wet = np.stack([signal.fftconvolve(pad, ir)[: len(pad)] for ir in irs], axis=1)
    dry = np.stack([pad, pad], axis=1)
    return dry * (1 - mix) + wet * mix * 0.9


def stereo(x, pan=None):
    """Mono zu Stereo. pan: Array oder Zahl zwischen -1 (links) und 1 (rechts)."""
    if pan is None:
        pan = 0.0
    p = (np.asarray(pan) + 1) / 2
    return np.stack([x * np.cos(p * np.pi / 2), x * np.sin(p * np.pi / 2)], axis=1) * np.sqrt(2)


def bell(freq, dur, decay, partials=((1, 1.0), (2.76, 0.35), (5.4, 0.15), (8.93, 0.06))):
    t = t_axis(dur)
    y = np.zeros_like(t)
    for ratio, amp in partials:
        y += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t / (decay / ratio ** 0.6))
    att = np.clip(t / 0.002, 0, 1)
    return y * att


def fit(x, dur):
    n = int(dur * SR)
    if x.ndim == 1:
        x = stereo(x)
    if len(x) < n:
        x = np.concatenate([x, np.zeros((n - len(x), 2))])
    x = x[:n]
    fade = int(0.02 * SR)
    x[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return x


def place(buf, x, t):
    i = int(t * SR)
    n = min(len(x), len(buf) - i)
    if n > 0:
        buf[i:i + n] += x[:n]


# ── die einzelnen Effekte ──────────────────────────────────────────────

def whoosh(dur=0.57, f0=350, f1=3200, peak=0.55, bright=1.0):
    n = int(dur * SR)
    x = noise(n)
    pos = np.linspace(0, 1, n)
    shape = lambda p: np.sin(np.pi * min(p / (2 * peak), 0.5)) if p < peak else 1 - 0.55 * (p - peak) / (1 - peak)
    y = bandpass_sweep(x, f0, f1 * bright, q=1.6, steps=96, shape=shape)
    amp = np.where(pos < peak, (pos / peak) ** 2.2, np.exp(-(pos - peak) / ((1 - peak) / 3.5)))
    y = y * amp
    pan = -0.6 + 1.2 * pos
    dry = stereo(y, pan)
    wet = reverb(y, size=0.5, mix=1.0)
    out = wet * 0.18
    out[:len(dry)] += dry * 0.82
    return out


def whoosh_cinematic(dur=5.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = noise(n)
    peak = 1.1
    swell = np.where(t < peak, (t / peak) ** 2.5, np.exp(-(t - peak) / 0.9))
    air = bandpass_sweep(x, 180, 1400, q=1.2, steps=128,
                         shape=lambda p: min(p * dur / peak, 1.0) if p * dur < peak else 1 - 0.7 * (p * dur - peak) / (dur - peak))
    sub_f = 70 + 40 * np.clip(t / peak, 0, 1)
    sub = np.sin(2 * np.pi * np.cumsum(sub_f) / SR) * 0.35
    y = (air + sub) * swell
    return reverb(y, size=2.4, mix=0.35, damp=3500)


def pop(dur=0.72):
    t = t_axis(0.12)
    f = 260 + 900 * np.exp(-t / 0.012)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.035)
    y += 0.25 * highpass(noise(len(t)), 2500) * np.exp(-t / 0.004)
    return reverb(y, size=0.4, mix=0.15)


def ping(dur=1.32):
    return reverb(bell(1568, 1.0, 0.16), size=0.6, mix=0.2)


def chime(dur=2.5):
    buf = np.zeros(int(dur * SR))
    for k, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
        place(buf, bell(f, 1.8, 0.28) * (0.9 - 0.1 * k), 0.09 * k)
    return reverb(buf, size=1.2, mix=0.3)


def click(soft=False):
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    tr = highpass(noise(n), 3000 if not soft else 1500) * np.exp(-t / (0.0012 if not soft else 0.002))
    body_f = 2300 if not soft else 1100
    body = np.sin(2 * np.pi * body_f * t) * np.exp(-t / (0.008 if not soft else 0.012)) * 0.6
    y = tr + body
    if soft:
        y = lowpass(y, 4500)
    return reverb(y, size=0.25, mix=0.1)


def key_once(pitch=1.0, level=1.0):
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    tick = highpass(noise(n), 2000) * np.exp(-t / 0.0015)
    thock = np.sin(2 * np.pi * 380 * pitch * t) * np.exp(-t / 0.012) * 0.7
    clack = signal.sosfilt(signal.butter(2, [2500 * pitch, 5200 * pitch], btype='band', fs=SR, output='sos'),
                           noise(n)) * np.exp(-t / 0.006) * 0.8
    return (tick * 0.6 + thock + clack) * level


def key_press(dur=0.4):
    buf = np.zeros(int(dur * SR))
    place(buf, key_once(1.0, 1.0), 0.0)
    place(buf, key_once(1.15, 0.45), 0.085)
    return reverb(buf, size=0.2, mix=0.08)


def typing(dur=1.5):
    buf = np.zeros(int(dur * SR))
    t = 0.0
    while t < dur - 0.12:
        place(buf, key_once(RNG.uniform(0.85, 1.2), RNG.uniform(0.55, 1.0)), t)
        if RNG.random() < 0.6:
            place(buf, key_once(RNG.uniform(1.1, 1.3), RNG.uniform(0.2, 0.35)), t + RNG.uniform(0.05, 0.07))
        t += RNG.uniform(0.07, 0.15) * (2.2 if RNG.random() < 0.08 else 1.0)
    return reverb(buf, size=0.2, mix=0.08)


def notification(dur=2.45):
    buf = np.zeros(int(dur * SR))
    marimba = ((1, 1.0), (3.93, 0.25), (9.2, 0.05))
    place(buf, bell(1318.5, 1.2, 0.16, marimba), 0.0)
    place(buf, bell(1760.0, 1.6, 0.22, marimba), 0.16)
    return reverb(buf, size=1.0, mix=0.25)


def error(dur=1.6):
    buf = np.zeros(int(dur * SR))
    for k, f in enumerate([440.0, 349.2]):
        t = t_axis(0.32)
        sq = signal.square(2 * np.pi * f * t) * 0.5 + np.sin(2 * np.pi * f * t) * 0.5
        y = lowpass(sq, 1800) * np.clip(t / 0.01, 0, 1) * np.exp(-t / 0.18)
        place(buf, y, 0.2 * k)
    return reverb(buf, size=0.8, mix=0.2)


def glitch(dur, seed):
    rng = np.random.default_rng(seed)
    buf = np.zeros(int(dur * SR))
    t = 0.0
    while t < dur * 0.8:
        seg = rng.uniform(0.02, 0.12)
        n = int(seg * SR)
        kind = rng.integers(3)
        tt = np.arange(n) / SR
        if kind == 0:
            y = signal.square(2 * np.pi * rng.uniform(80, 900) * tt) * 0.6
        elif kind == 1:
            y = np.round(rng.standard_normal(n) * 3) / 3
            y = lowpass(y, rng.uniform(1500, 9000))
        else:
            y = np.sin(2 * np.pi * rng.uniform(1500, 6000) * tt) * signal.square(2 * np.pi * rng.uniform(20, 70) * tt)
        k = int(rng.integers(1, 6))                      # Sample-and-hold = Bitcrusher-Effekt
        y = np.repeat(y[::k], k)[:n]
        y = np.pad(y, (0, n - len(y)))
        y *= np.hanning(n) ** 0.2
        place(buf, y * rng.uniform(0.4, 1.0), t)
        t += seg + (rng.uniform(0.0, 0.25) if rng.random() < 0.35 else 0)
    pan = np.sin(np.arange(len(buf)) / SR * rng.uniform(4, 9)) * 0.6
    return stereo(buf, pan)


def impact(dur, f_start, f_end, decay, seed):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f_end + (f_start - f_end) * np.exp(-t / 0.06)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / decay)
    sub = np.tanh(sub * 3.0) / np.tanh(3.0)
    hit = lowpass(rng.standard_normal(n), 2500) * np.exp(-t / 0.02) * 0.7
    y = sub + hit
    return reverb(y, size=1.6, mix=0.22, damp=2500)


def riser(dur=10.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    f = 110 * 2 ** (3.0 * p ** 1.6)
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = sum(np.sin(k * ph) / k for k in range(1, 9)) * 0.35
    det = sum(np.sin(k * ph * 1.006) / k for k in range(1, 9)) * 0.35
    air = bandpass_sweep(noise(n), 400, 9000, q=1.4, steps=160, shape=lambda q: q ** 1.5) * 0.9
    amp = (p ** 1.3)
    trem = 1 + 0.25 * np.sin(2 * np.pi * (2 + 14 * p ** 2) * t) * p
    y = (saw + det + air) * amp * trem
    y[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
    pan = 0.3 * np.sin(2 * np.pi * 0.3 * t)
    return stereo(y, pan)


def sparkle(dur=1.8):
    buf_l = np.zeros(int(dur * SR))
    buf_r = np.zeros(int(dur * SR))
    for _ in range(26):
        f = RNG.uniform(2400, 7200)
        st = RNG.uniform(0, 0.75) ** 1.4
        y = bell(f, 0.9, RNG.uniform(0.12, 0.35), ((1, 1.0), (2.01, 0.2))) * RNG.uniform(0.3, 1.0)
        pan = RNG.uniform(-0.9, 0.9)
        place(buf_l, y * np.cos((pan + 1) * np.pi / 4), st)
        place(buf_r, y * np.sin((pan + 1) * np.pi / 4), st)
    shimmer = highpass(noise(len(buf_l)), 6000) * env_adsr(len(buf_l), 0.05, 0.4) * 0.12
    x = np.stack([buf_l + shimmer, buf_r + shimmer], axis=1)
    return np.stack([reverb(x[:, 0], 1.0, 0.3)[:, 0], reverb(x[:, 1], 1.0, 0.3)[:, 1]], axis=1)


EFFECTS = {
    'whoosh': (lambda: whoosh(0.57, 300, 2800, 0.55), 0.575),
    'whoosh-short': (lambda: whoosh(0.57, 500, 4200, 0.45), 0.575),
    'whoosh-cinematic': (whoosh_cinematic, 5.54),
    'pop': (pop, 0.72),
    'ping': (ping, 1.32),
    'chime': (chime, 2.5),
    'click': (lambda: click(False), 0.37),
    'click-soft': (lambda: click(True), 0.37),
    'key-press': (key_press, 0.4),
    'typing': (typing, 1.5),
    'notification': (notification, 2.45),
    'error': (error, 1.6),
    'glitch-1': (lambda: glitch(2.6, 1), 2.64),
    'glitch-2': (lambda: glitch(3.5, 2), 3.5),
    'glitch-3': (lambda: glitch(3.1, 3), 3.1),
    'impact-bass-1': (lambda: impact(2.1, 160, 46, 0.55, 11), 2.12),
    'impact-bass-2': (lambda: impact(2.6, 120, 38, 0.8, 12), 2.6),
    'riser': (riser, 10.03),
    'sparkle': (sparkle, 1.8),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for name, (fn, dur) in EFFECTS.items():
            x = fit(fn(), dur)
            x = x / (np.abs(x).max() + 1e-9) * 10 ** (-1 / 20)   # Spitze −1 dBFS
            wav = os.path.join(tmp, name + '.wav')
            wavfile.write(wav, SR, (x * 32767).astype(np.int16))
            dst = os.path.join(OUT, name + '.mp3')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-b:a', '192k',
                            '-map_metadata', '-1', dst], check=True)
            print(f'{name:18s} {dur:5.2f} s')


if __name__ == '__main__':
    main()
