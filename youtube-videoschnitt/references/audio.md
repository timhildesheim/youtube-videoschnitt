# Ton: Stimme, Musik, Sound-Effekte

## Stimme: Standard ist das Original
`profil.ton.stimme_fx = "anull"` → mix.py übernimmt die Stimme unverändert, assemble.py hebt nur den Pegel auf
`profil.ton.ziel_lufs` an und fängt Spitzen bei −1,5 dBFS ab. Erfahrung aus der Praxis: Bei sauberen Aufnahmen
klingt das Original meist am besten; „Podcast-Ketten“ machen Raumklang schnell hörbar.
Eine Kette nur, wenn die Person es wünscht – vorher eine **lautheitsangeglichene Hörprobe** bauen
(Original | Pause | neu, je ~20 s, `loudnorm=I=-16`) und vorspielen. Die gewählte Kette dann in
`profil.ton.stimme_fx` (für alle Videos) oder `project.json → "voice_fx"` (nur dieses Video) speichern.

### Erprobte Kette „warm, trocken“ (Referenz)
| Filter | Zweck |
|---|---|
| `highpass=f=70` | Trittschall, Brummen |
| `agate=threshold=<p80−10 dB>:ratio=3:attack=2:release=90:range=0.15` | Expander: senkt Raum-Ausklänge zwischen Wörtern (Schwelle aus dem Sprachpegel berechnen) |
| `equalizer=f=170:w=1:g=1.5` | Wärme, Nähe |
| `equalizer=f=380:w=1.1:g=-3` | Raum/Boxigkeit raus |
| `equalizer=f=2800:w=1.2:g=1.5` | sanfte Präsenz (nicht mehr – Präsenz und Luft machen Hall hörbarer) |
| `deesser=i=0.4` | S-Laute |
| `acompressor=threshold=0.1:ratio=2.5:attack=10:release=200:makeup=1.6` | gleichmäßiger, ohne leise Hallfahnen hochzuziehen |
| `lowpass=f=14000`, `alimiter=limit=0.8` | weiche Höhen, Spitzen |

Gemessen: Nachklang −17,5 dB (vorher −12,6). **Was nicht funktioniert hat:** Präsenz +3 dB, Luft +2 dB @9 kHz und
Kompressor 3,5:1 mit Makeup → Nachklang −7,6 dB, also deutlich halliger. WPE-Enthallung und DeepFilterNet bringen bei
rauschfreien Aufnahmen praktisch nichts. Stärkerer Expander (ratio 4, range −20 dB) hackt Wortenden ab.
Messen mit `voice_check.py` auf ein 45-s-Stück vor/nach der Kette: Nachklang muss sinken. Rauscht eine Aufnahme,
vorne `afftdn=nr=10:nf=-45` ergänzen.

## Musik (nur wenn `profil.ton.musik`)
- Lokal mit MusicGen (medium) komponiert → keine fremden Aufnahmen, deshalb keine Content-ID-Treffer zu erwarten. Die
  Modell-Gewichte stehen unter CC-BY-NC 4.0 (siehe README, Abschnitt Lizenzen). Stimmungen in `music.py`:
  `intro` (optimistisch, Gitarre, 110 bpm), `work` (Lo-fi, Rhodes, 88 bpm), `reveal` (cinematic, Piano, 90 bpm),
  `outro` (warm Deep House, 118 bpm), `tension` (neugierig, Synth). Eigene Stimmungen in `profil.ton.musik_stimmungen`
  oder per `name:prompt=sekunden`.
- **Nicht durchgehend.** Fenster typischerweise:
  | Szene | Stimmung | unter Sprache / in Pausen |
  |---|---|---|
  | Intro bis Screen-Start | intro | −21 / −15 |
  | Warte-/Arbeitsphasen („ich lasse die KI arbeiten“), Durchklicken | work | −25 / −18 |
  | Ergebnis-Reveal | reveal | −24 / −16 |
  | Zwischenmoderation im Vollbild | intro (Offset 40 s) | −23 / −16 |
  | Recap + Outro + Endkarte | outro (`"to": "end"`) | −23 / −16 |
  Diktat von Prompts und dichte Erklärpassagen bleiben ohne Musik. Läuft in der Aufnahme schon Musik (Spiel, Demo),
  dort keine eigene Musik und keine Sound-Effekte (`references/pitfalls.md`).
- Ziel: Musik **13–18 LU unter der Stimme**. Prüfen mit
  `ffmpeg -ss <t> -t 60 -i stem_music.wav -af ebur128=framelog=quiet -f null -` vs. `stem_voice.wav`.
- Ducking automatisch über die Sprachhüllkurve (40 ms Attack / 600 ms Release), Ein-/Ausblenden 1,2 s / 3 s.
- `music.py` schneidet Aussetzer automatisch heraus; trotzdem einmal den Pegelverlauf pro Sekunde ansehen.

## Sound-Effekte (assets/sfx, selbst synthetisiert und frei nutzbar; nur wenn `profil.ton.sfx`)
whoosh / whoosh-short / whoosh-cinematic, pop, click, click-soft, ping, chime, sparkle, typing, riser, impact-bass …
Werden von den Komponenten automatisch gesetzt; Pegel dezent, Gesamtlautstärke über `profil.ton.sfx_pegel`.
Eigene Sounds: einfach eine Datei gleichen Namens (mp3) in `assets/sfx/` ablegen, mix.py normalisiert jede Datei auf
dieselbe Spitze.

## Master
assemble.py: nur Pegel auf `ziel_lufs` (Standard −14 LUFS, YouTube-Referenz) + Spitzenbegrenzer bei −1,5 dBFS, AAC 320 kbit/s.
