# Gast-Format: Opener, Marken-Intro, Steckbrief, Ortsmarke

Für Kanäle, die Menschen porträtieren (Interview/Porträt). Aktiv, wenn `profil.einblendungen.intro` bzw.
`.steckbrief` / `.ortsmarke` true sind. Reihenfolge im fertigen Video:

```
[Cartoon-/Erklär-Opener 1–2 min, optional]  →  [Marken-Intro ≈ 6 s, ÜBER dem Interview-Anfang]  →  Interview
                                                 └ Jingle als Musikfenster        └ Steckbrief, sobald der Gast vorgestellt ist
```

## Gast-Daten in project.json
Vor dem Storyboard bei der Person erfragen (oder aus dem Transkript ableiten und bestätigen lassen):
```json
"gast": {
  "name": "Anna Beispiel",
  "name_betont": "Anna *Beispiel*",
  "rolle": "Goldschmiedin",
  "steckbrief_rolle": "Goldschmiedin aus Plagwitz",
  "folge": 3,
  "ort": {"label": "Plagwitz", "detail": "Werkstatt in der Karl-Heine-Straße"},
  "fakten": [["Seit", "2009 selbstständig"], ["Stadtteil", "Plagwitz"], ["Fun Fact", "Trägt selbst keinen Schmuck"]]
}
```
`intro()`, `steckbrief()` und `ortsmarke()` nehmen diese Werte, wenn keine Argumente übergeben werden.

## Marken-Intro – `c.intro(cid, t0, gast=None, rolle=None, folge=None, titel=None, dur=6.4)`
- Liegt **über** dem laufenden Video: Bild dunkelt ab und verschwimmt, ein schräger Akzent-Strich (wie im Logo) zieht
  durch, Logo + Kanalname steigen ein, feine Akzentlinie, Zeile „Folge n / **Gast**, Rolle“, Abgang als schräger
  Doppel-Wisch (Akzent + Basis), der das Video freigibt.
- **Skyline** (`profil.marke.skyline`, z. B. `leipzig`): feine Linien-Silhouette der Stadt zeichnet sich unten von links
  nach rechts ins Bild und driftet langsam; auch dezent auf der Endkarte. `skyline=False` schaltet sie im Intro ab.
  Eigene Skyline: SVG (viewBox 1920×300, Linien mit `stroke="currentColor"` und `pathLength="1"`) in den Profilordner
  legen und den Dateinamen eintragen.
- Platz: direkt nach dem Opener bzw. nach dem Hook/Cold Open (erste 10–40 s). Nicht über einen wichtigen Satz legen –
  eine Stelle wählen, an der der Gast z. B. ankommt, die Werkstatt zeigt oder eine Pause ist. Der Ton läuft weiter.
- Im selben Segment keine andere Einblendung in den 6,4 s. In `th`-Segmenten zusätzlich `th_pushins()` wie immer.
- Akzentfarbe ist hier ausdrücklich erlaubt (Markenmoment), sonst bleibt sie der CTA-Pille vorbehalten.

### Jingle
- Profil: `ton.intro_jingle` = Dateiname im Profilordner (z. B. `intro-jingle.mp3`), einmal erzeugt und in jeder
  Folge wiederverwendet. Empfehlung: über den media-skill mit **Suno** (kommerzielle Nutzung mit bezahltem Suno-Plan;
  MusicGen-Gewichte sind CC-BY-NC und für monetarisierte Kanäle riskant). Prompt-Vorschlag: „short punchy 8 second
  YouTube intro sting, modern urban documentary, warm analog synth stab, tight drum fill, confident, ends on a clean
  hit, no vocals“. Die ersten ~7 s ausschneiden, kurze Ausblendung.
- Musikfenster in project.json (Quellzeit wie immer, `from` = Intro-Start):
  `{"track": "jingle", "from": 41.0, "to": 47.4, "fade_in": 0, "fade_out": 0.8, "tail": 0.6, "gap_db": -9, "speech_db": -15}`
  Ohne `file` nimmt `track: "jingle"` die Datei aus `ton.intro_jingle`. Eigene Dateien gehen mit `"file": "…"`
  (absolut, im Profilordner oder im Arbeitsordner). Musik mit `file` wird nicht geloopt.
- Liegt kein Jingle vor: Fenster weglassen, das Intro trägt mit seinen Sound-Effekten (Whoosh, Bass-Impact, Wisch).

## Steckbrief – `c.steckbrief(cid, t0, t1, name=None, rolle=None, fakten=None, w=620)`
- Freier Text auf der Seite **gegenüber dem Gesicht** (automatisch aus `layout.face`): kleines Label mit schrägem
  Akzentstrich, Name groß (ein Teil mit `*…*` betont), Rolle, darunter 3–5 Zeilen „Label · Wert“ mit feinen Linien.
- Zeitpunkt: wenn der Gast sich vorstellt oder vorgestellt wird (`words.py "ich bin" "mein Name"`), 6–9 s stehen lassen.
- `fakten` als `[(Label, Wert)]` (erscheinen nacheinander) oder `[(Ausgabezeit, Label, Wert)]` (erscheinen, wenn sie
  gesagt werden). Werte kurz (max. ~28 Zeichen), ein Fun Fact macht's persönlich.
- Bei zwei Personen im Bild: `pos={'left':…, 'top':…}` setzen, sodass kein Gesicht verdeckt wird (check_layout.py).

## Ortsmarke – `c.ortsmarke(cid, t0, t1, label=None, detail=None, stadt=None, pos=None)`
- Schlanker Pin mit Pulsring, Stadtname klein darüber, Ortsteil groß, Detailzeile darunter – unten links (Standard)
  oder an `pos`. Für Ortswechsel (neue Location, Außendreh) und einmal am Anfang nach dem Intro.
- `stadt` Standard aus `profil.kanal.stadt` (z. B. „Leipzig“).
