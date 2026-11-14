"""Stimme messen: Nachhall nach Wortenden, Pausenpegel, Klangbalance. Für das Abstimmen der Stimmkette.

    ~/.cache/youtube-videoschnitt/mgenv/bin/python voice_check.py datei1.wav datei2.wav …

Nachklang = Pegel 50–250 ms nach einem Wortende relativ zum Wort (dB). Je negativer, desto trockener.
Richtwerte aus einer früheren Produktion: Original −12,6 dB, Ziel ≤ −16 dB. Nie eine Kette nehmen, die den Wert anhebt
(Kompressor mit viel Makeup + Höhenanhebung tut genau das). Bänder relativ zur Gesamtenergie.
"""
import sys
import numpy as np, soundfile as sf

for fn in sys.argv[1:]:
    a, sr = sf.read(fn, always_2d=True)
    a = a.mean(1)
    h = sr // 100
    k = len(a) // h
    db = 20 * np.log10(np.sqrt((a[:k * h].reshape(k, h) ** 2).mean(1)) + 1e-9)
    sp = np.percentile(db, 80)
    tails = [db[i + 5:i + 25].mean() - db[i - 10:i].mean() for i in range(10, k - 30)
             if db[i - 10:i].mean() > sp - 8 and db[i + 3] < db[i - 1] - 12]
    S = np.abs(np.fft.rfft(a)) ** 2
    f = np.fft.rfftfreq(len(a), 1 / sr)
    tot = S[(f > 50) & (f < 20000)].sum()
    bands = ' '.join(f'{lo}-{hi}:{10*np.log10(S[(f>=lo)&(f<hi)].sum()/tot):.1f}' for lo, hi in
                     [(100, 200), (200, 500), (1600, 3200), (3200, 6400), (6400, 12000)])
    print(f'{fn}\n  Sprachpegel p80 {sp:.1f} dBFS · Nachklang {np.mean(tails):.1f} dB (n={len(tails)}) · '
          f'Pausen {np.median(db[db < sp - 20]) - sp:.1f} dB\n  Bänder {bands}')
