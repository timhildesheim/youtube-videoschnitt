# Cartoon-/Erklär-Opener (1–2 Minuten) über den Gast

Ein kurzer, unterhaltsamer Film vor dem Interview: Wer ist die Person, was macht sie, was ist das Besondere?
Ergebnis `<Videoordner>/opener.mp4`; `assemble.py` stellt ihn automatisch voran (abschalten: `"opener": false` in
project.json), `export_texts.py` verschiebt Transkript-Zeiten um seine Länge. **Kapitelmarken** ebenfalls um
`project.json → opener_sec` verschieben, erstes Kapitel „0:00 Wer ist …?“ für den Opener.

## Ablauf
1. **Material sammeln** (fragen): 3–6 Fakten zum Gast, eine Anekdote/ein Twist, 1–3 Fotos der Person (für die Figur),
   Fotos vom Arbeitsort. Was darf nicht gezeigt werden?
2. **Drehbuch** schreiben: 10–16 Szenen à 4–8 s, Sprechertext je Szene 1–2 kurze Sätze (≈ 2,3 Wörter/s), Aufbau
   Hook (ungewöhnlichste Tatsache zuerst) → Werdegang in 3–4 Bildern → was sie heute macht → Twist/Pointe → Überleitung
   („… und genau darüber sprechen wir heute.“). Ton: warm, augenzwinkernd, nie über die Person lustig machen.
   `opener/drehbuch.md` anlegen und **von der Person freigeben lassen**, bevor Bilder erzeugt werden.
3. **Stil festlegen** (einmal pro Kanal, dann ins Profil `bilder.opener_stil`): Beispiel für eine Petrol-Creme-Orange-
   Marke: flache 2D-Illustration, kräftige Konturen, begrenzte Palette aus den Markenfarben (Petrol, Creme, Orange),
   leichte Papierstruktur. Prompt-Baustein (englisch):
   `flat 2D editorial cartoon illustration, bold clean outlines, limited palette of deep petrol #101d23, warm cream
   #f2eee3 and signal orange #ee562f with muted teal accents, subtle paper grain, friendly expressive characters,
   16:9 composition with empty space bottom-left for a caption, no text in image`.
4. **Figur**: aus einem Foto des Gastes zuerst ein **Figurenblatt** (Vorder-/Seitenansicht, 2–3 Ausdrücke) mit
   GPT Image 2 image-to-image oder Nano Banana erzeugen und freigeben lassen. Jede Szene dann mit dem Figurenblatt als
   Referenzbild erzeugen – so bleibt die Figur gleich. Keine Szene ohne Referenz.
5. **Szenenbilder**: über den media-skill (`kie.py erzeugen`, Kosten vorher mit `kie.py preis` zeigen). 2K reicht
   (Bilder werden auf 1920×1080 gezeigt, Kamerafahrt zoomt bis 1,16). Für Parallax optional eine Vordergrund-Ebene als
   PNG mit Transparenz.
6. **Bewegte Schlüsselszenen** (optional, 2–4 Stück): aus dem Szenenbild mit grok-imagine (günstig) oder Kling 3.0
   (beste Bewegung) einen 5–6-s-Clip machen. Prompts auf Englisch. Rest bleibt Standbild mit Kamerafahrt.
7. **Sprecher**: am besten die eigene Stimme (authentisch, kostenlos): Text aus dem Drehbuch einsprechen,
   `voiceover.wav`. Alternativ ElevenLabs multilingual v2 über den media-skill. Szenendauern an den Sprecher anpassen.
8. **Musik**: verspielt-dokumentarisch, unter dem Sprecher (opener.py senkt sie automatisch ab). Suno über den
   media-skill (`kie.py musik`). MusicGen (lokal) nur für nicht monetarisierte Videos (CC-BY-NC).
9. `opener/opener.json` schreiben (Format im Kopf von `scripts/opener.py`), dann
   `~/.cache/youtube-videoschnitt/mgenv/bin/python $SK/scripts/opener.py <Videoordner>/opener --vorschau` (ein
   Kontrollbild pro Szene) und ohne `--vorschau` rendern (≈ 4–8 min für 90 s).

## Gestaltung (opener.py)
- Szenen wechseln mit dem Akzent-Wisch (wie im Marken-Intro), Comic-Texte auf schräger dunkler Plakette, Wörter
  ploppen nacheinander rein, betonte Wörter (`*…*`) in Akzentfarbe. Pro Szene höchstens eine Textzeile – der Sprecher
  erzählt, der Text setzt Pointen (Zahl, Name, Ort, Twist).
- Schluss: Akzent- und Basis-Wisch füllen das Bild → direkt danach das Marken-Intro über dem Interview-Anfang.

## Kosten grob (kie.ai, Stand Nov. 2026, vor jedem Lauf mit `kie.py preis` neu rechnen)
| Posten | Menge | Credits |
|---|---|---|
| Figurenblatt + Szenen, GPT Image 2 2K | ~16 Bilder × 10 | ~160 |
| Bewegte Szenen, grok-imagine 720p / Kling 3.0 720p | 4 × 5 s × 4,5 / × 14 | ~90 / ~280 |
| Sprecher ElevenLabs (falls nicht selbst gesprochen) | ~1.500 Zeichen | ~18 |
| Musik Suno | 1 Anfrage | wenige Credits (Preisseite prüfen) |
| **Summe** | | **≈ 270–460 Credits ≈ 1,20–2,00 €** pro Folge |
