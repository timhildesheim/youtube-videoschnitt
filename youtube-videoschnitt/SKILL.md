---
name: youtube-videoschnitt
description: Schneidet fertig aufgenommene YouTube-Videos komplett in 4K – Pausen und Versprecher raus, Jump-Cuts/Push-ins, Motion Graphics im eigenen Designsystem per HyperFrames (cleaner freier Text in einer Schrift statt Kacheln, langsames Laufband hinter der Person, Kapitel-Titelkarten mit Kinobalken, Learnings, Listen, Zooms), CTA-Einblendung (Community, Newsletter, Produkt), animierter Abo-Störer, lokal komponierte Musik nur in passenden Szenen, Sound-Effekte, Stimme im Original, −14 LUFS, optional Werbepartner-Einblendungen mit Werbekennzeichnung und Export als DaVinci-Resolve-Timeline, plus Kapitelmarken und geschnittenes Transkript. Beim ersten Einsatz führt der Skill ein Einrichtungsinterview (Kanal, Marke, Farben, Schriften, CTA, Aufnahme-Setup, Ablage, Ton, Bilder) und speichert ein Profil. Verwenden, sobald jemand ein Video (oder einen Ordner mit .mp4/.mov) schneiden, bearbeiten, „aufhübschen“, mit Einblendungen/Motion Graphics/Overlays versehen oder für YouTube fertig machen will – und wenn jemand den Videoschnitt-Skill einrichten, neu einrichten oder sein Profil ändern möchte.
---

# YouTube-Videoschnitt mit Motion Graphics

Aus einer fertigen Aufnahme wird ein fertiges 4K-Video mit Einblendungen im Stil des Kanals, plus Kapitelmarken und
geschnittenem Transkript. Alles Kanalspezifische (Marke, Farben, Schriften, CTA, Ablage, Vorlieben) steht im
**Profil**, nicht in diesem Skill.

Skill-Ordner (im Folgenden `$SK`): der Ordner dieser Datei, meist `~/.claude/skills/youtube-videoschnitt/`.
Skripte in `$SK/scripts`, mitgelieferte Assets (GSAP, Standardschriften, Sound-Effekte) in `$SK/assets`.
Profil: `~/.config/youtube-videoschnitt/profil.json` mit Schrift, Logo, Kanalbild und Werbepartnern daneben
(anderer Ort über die Umgebungsvariable `YTV_PROFIL`).

## Schritt −1 · Profil vorhanden?
`python3 $SK/scripts/profil.py` ausführen.
- **Kein Profil** → zuerst das **Einrichtungsinterview** aus `references/einrichtung.md` führen, auch wenn schon
  ein Video genannt wurde („Bevor ich schneide, richte ich den Skill kurz für deinen Kanal ein – dauert 10–15 Minuten.“).
- Profil da → `profil.json` **vollständig lesen**, besonders `wuensche` (Regeln aus früherem Feedback), `schreibstil`,
  `ablage`, `cta`, `aufnahme.setups`. Diese Vorgaben gelten für das ganze Video.
- „Einrichten“, „neu einrichten“, „Profil ändern“ → `references/einrichtung.md`, Abschnitt „Später ändern“.
- **Profil aus Version 1** (`version` fehlt oder 1): kurz auf Version 2 heben. Neue Felder ergänzt profil.py selbst
  aus der Vorlage. Von Hand: `version: 2`, `marke.schriften.akzent` leeren (Clean-Stil nutzt eine Schrift),
  `marke.radius`/`glas_blur`/`bilder.icon_stil` können weg, `aufnahme.rahmen_radius` erfragen (Block 4.5 im Interview).
  Danach `setup_profil.py` und `vorschau.py`, die Vorschau zeigen.

## Grundregeln (gelten immer, sofern das Profil nichts anderes sagt)
- **4K bleibt 4K.** Ausgabe 3840×2160, 30 fps. Das Original wird nie verändert.
- **Clean statt KI-Look**: eine Schrift aus dem Profil (Headlines 600 mit −0,04 em, Text 400), Text frei im Bild mit
  weichem Schatten, **keine Kacheln, keine Icons neben Text**, Aufzählungen als Text untereinander. Flächen nur für
  echte Objekte (Screenshot, Suchleiste, Abo-Button, CTA-Pille). Ruhige, filmische Bewegung (Wörter steigen mit
  Unschärfe ein, Kapitel mit Kinobalken, Text hinter der Person läuft langsam). Farben aus dem Profil, Akzent nur für
  CTA-Pille und „Abonniert“. Regeln in `references/design-system.md`; keine eigenen Stile erfinden.
- **CTA** (`profil.cta`) immer dann einblenden, wenn die Person ihn erwähnt (Stichworte in `cta.stichworte`) –
  groß, mit frischem Screenshot der Seite, Pille aus `cta.pille`. Im Outro `outro_cta`.
- **Abo-Störer** (`profil.abo_stoerer`): in jedem Video an einer ruhigen Stelle nach dem Hook, bei `anzahl: 2`
  zusätzlich bei ~60 %. Spricht die Person selbst übers Abonnieren, genau dort.
- **Schnitt**: Sprechpausen und Hänger raus, im Vollbild-Talking-Head Push-ins an jedem Schnitt. Inhalte nur kürzen,
  wenn `schnitt.inhalt_kuerzen` es erlaubt – nie mitten im Satz schneiden, um eine Ziellänge zu treffen.
- **Musik** lokal komponiert, nicht durchgehend (Intro, Outro, Reveals, Arbeitsphasen), nur wenn `ton.musik`.
  Sound-Effekte dezent, nur wenn `ton.sfx`.
- **Gast-Format** (wenn `einblendungen.intro`/`steckbrief`/`ortsmarke` an sind): Gast-Daten in `project.json → gast`
  erfragen, Marken-Intro über den Interview-Anfang (nach Opener/Hook) mit Jingle (`ton.intro_jingle`), Steckbrief beim
  Vorstellen, Ortsmarke bei Ortswechseln. Ein fertiger Opener (`opener.mp4` im Videoordner, `references/opener.md`)
  wird vorangestellt. Ablauf und Regeln: `references/intro-steckbrief.md`.
- **Kamera bleibt scharf**, wenn der Hintergrund für eine große Einblendung geblurrt wird.
- **Lesbarkeit**: hinter frei schwebender Schrift lokal blurren.
- **Stimme** nach `ton.stimme_fx` (Standard: Original). Nur der Gesamtpegel wird auf `ton.ziel_lufs` gebracht.
- **Bilder** nur, wenn sie etwas zeigen (Screenshot, generiertes Foto, Mockup), und nur mit dem Werkzeug aus
  `profil.bilder` (`references/assets.md`). Ohne Generator: Screenshots.
- **Feedback** der Person nach einem Video als kurze Regel in `profil.json → wuensche` ergänzen (und, wenn es
  Design/Ton betrifft, im passenden Profilfeld), damit es beim nächsten Video automatisch gilt.

## Ablage
Videos liegen in `profil.ablage.wurzel` (leer = der Ordner, auf den die Person zeigt), ein Unterordner pro Video.
„Bearbeite das XY-Video“ heißt: passenden Ordner suchen (neuester mit unbearbeiteter .mp4/.mov), bei mehreren
Treffern nachfragen. Dort wird gearbeitet, dort landet das Ergebnis:

```
<Videoordner>/
├── <Hauptvideo>.mp4                 ← Original, wird nie verändert
├── <… Kamera only>.mp4              ← optionale Kameraspur (Namen in aufnahme.kamera_spur.erkennung)
├── <ablage.ergebnis>                ← ERGEBNIS, z. B. „<Hauptvideo> – fertig 4K.mp4“
├── <ablage.kapitel_datei>           ← Kapitel in Schnittzeit, kopierfertig
├── <ablage.transkript_datei>        ← Transkript mit Zeitmarken des fertigen Videos
└── <ablage.arbeitsordner>/          ← Arbeitsordner aller Skripte (25–30 GB, nach Abnahme löschbar)
```
- **Hauptvideo** = die Datei ohne Kamera-Kennung im Namen. Mehrere Hauptvideos → nachfragen.
- **Nicht überschreiben:** alles aus `ablage.geschuetzt`. Einzige Ausnahme: `ablage.beschreibung_datei` enthält
  Kapitelzeiten – die stimmen nach dem Schnitt nicht mehr. Dann Kopie `<Datei> (vor Schnitt)` anlegen und nur den
  Kapitelblock ersetzen (`references/description.md`).

## Bezahlte Werbepartnerschaft
Ist das Video eine Kooperation, `"sponsor": "<partner>"` in `project.json` setzen (Partnerdaten, Logos, Rabattcode in
`~/.config/youtube-videoschnitt/partner/<partner>/`). Dann gibt es die Bausteine `sponsor()` (große weiße Einblendung
mit getipptem Rabattcode) und `sponsor_link()`, und `assemble.py` kennzeichnet das Video oben rechts mit „Werbung“.
Platzierung, Kennzeichnung und Brief-Checkliste: **`references/werbepartner.md`** vollständig lesen.

## Ablauf
Alle Skripte laufen **im Arbeitsordner** `<Videoordner>/<ablage.arbeitsordner>/`. Mehrere Videos nacheinander
abarbeiten (Rendern belegt die Maschine). Zwischendurch kurze Zwischenstände geben – ein 30-Minuten-Video dauert
insgesamt ~2–3 Stunden.

### 0 · Umgebung prüfen
`bash $SK/scripts/check_env.sh` – richtet Whisper-Modell und Python-Umgebung (`~/.cache/youtube-videoschnitt/mgenv`)
bei Bedarf ein und prüft das Profil. Rund 25–30 GB freien Platz pro 30-Minuten-Projekt einplanen.

### 0b · Gast-Format (wenn `einblendungen.intro`/`steckbrief` an)
Gast-Daten für `project.json → gast` erfragen (Name, Rolle, Folge, Ort, 3–5 Fakten) – `references/intro-steckbrief.md`.
Opener gewünscht? Dann parallel zum Schnitt `references/opener.md` (Drehbuch freigeben lassen, Bilder kosten Credits).

### 1 · Video untersuchen und transkribieren
`mkdir -p "<Videoordner>/<arbeitsordner>" && cd "$_" && python3 $SK/scripts/prepare.py "../<Hauptvideo>.mp4"` →
`project.json` (Grundgerüst, Layout aus dem ersten Profil-Setup vorbelegt), Transkript (`transcript/lines.txt`),
Kontaktbögen (`frames/contact_*.jpg`), Layout-Wechsel (`frames/scenes.txt`).
Lies `lines.txt` vollständig – die Einblendungen müssen inhaltlich auf den Punkt sitzen.

### 2 · Layout bestimmen und project.json ausfüllen
Kontaktbögen und einzelne Frames ansehen (`ffmpeg -ss <t> -i … -frames:v 1 -vf scale=1600:-1 …`) und eintragen:
- `talking_head_ranges`: Abschnitte, in denen die Person **vollformatig** spricht (frame-genau, `references/layouts.md`).
- `layout`: Typ und Lage von Kamera und Bildschirm in CSS-px (1920×1080). Bekannte Setups stehen in
  `profil.aufnahme.setups` – trotzdem am Video prüfen. Neues Setup → vermessen und ins Profil übernehmen.
- `layout.face`: Gesichtsmitte im Vollbild-Talking-Head (für Push-ins).
- `demo_ranges`: Stellen, an denen das Bild in Sprechpausen wichtig ist (Website scrollen, Ergebnis zeigen) – dort
  Pausen länger stehen lassen (1,2–2,6 s).
- `manual_remove`: Versprecher und Wiederholungen, Quellzeit von–bis.
- Optional: `force_keep` (Bereiche, die nie gekürzt werden), `thr_db`/`loud_db` (feste Pegelschwellen, falls leise
  Wortanfänge abgeschnitten werden), siehe Kopf von `edl.py`.

### 2b · Vollbild-Kamera-Einschübe (wenn eine Kameraspur da ist)
Die Kameraspur hat oft keinen oder stummen Ton – synchronisiert wird über das Bild:
`python3 $SK/scripts/sync_cam.py "../<Hauptvideo>.mp4" "../<Kameraspur>.mp4"` vergleicht die Bewegung der Person in
beiden Dateien und trägt `camera.offset` (und `camera.file`) ein. Danach den **Bildausschnitt** messen, damit
Einschübe exakt wie die Vollbild-Kamera-Szene des Hauptvideos aussehen:
`python3 $SK/scripts/match_crop.py "../<Hauptvideo>.mp4" "../<Kameraspur>.mp4" <3–6 Zeitpunkte im Vollbild>` →
`camera.crop`. Den Wert ins Profil (`aufnahme.kamera_spur.crop`) übernehmen – er gilt, solange sich die Szene nicht ändert.
Erwartung: gleicher Versatz in allen Fenstern (Drift ≤ 1 Frame), Konfidenz ≥ 3. Danach in `camera_cuts` (Quellzeit)
die Stellen eintragen, an denen auf Vollbild-Kamera geschnitten wird – starke Aussagen, Hook, Recap, Übergänge,
3–15 s lang, 3–8 pro Video. Sie zählen als Talking Head. Im Storyboard dafür `th`-Segmente mit
`th_pushins(face=CFG['camera']['face'])`. Kontrolle: Standbilder je 1 Frame vor/nach jedem Einschub – Kopfhaltung
und Mund müssen übereinstimmen. Springt der Versatz zwischen Einschüben (die Aufnahmesoftware hat Frames verloren),
je Einschub messen und als `camera_cut_offsets` (Liste, gleiche Reihenfolge wie `camera_cuts`) eintragen.

### 3 · Schnitt
`python3 $SK/scripts/edl.py` → Pausen gekürzt, `timemap.json` (Quellzeit → Schnittzeit), `voice_cut.wav`.
„Laute Stellen weggeschnitten“ muss 0 sein (außer manuellen Entfernungen). Schnitte richten sich nach dem **Pegel**,
nicht nach Whisper-Wortzeiten (±0,3 s ungenau).

### 4 · Basisvideo
`python3 $SK/scripts/render_base.py` (im Hintergrund, ~15–25 min) → `base.mp4` in 4K ohne Ton.

### 5 · Assets vorbereiten (parallel zu 4)
- CTA-Screenshot frisch aufnehmen: `node $SK/scripts/shots.mjs <cta.screenshot_url oder cta.url> cta` → `assets/cta.jpg`.
- Screenshots weiterer Seiten, über die die Person spricht, genauso.
- Keine Icons erzeugen. Mit Bildgenerator plakative Fotos/Illustrationen nur dort, wo sie ein Thema wirklich zeigen
  (Hook, Kapitelstarts, Ziel/Ergebnis; `references/assets.md`), mehrere Läufe parallel, während render_base.py läuft.
  Projektspezifische Bilder nach `<arbeitsordner>/assets/` legen; build.py verlinkt sie automatisch.

### 6 · Storyboard schreiben
`cp $SK/assets/story_template.py story.py` und ausarbeiten. Vorher **`references/storyboard-guide.md`** (Dichte,
was eingeblendet wird, Platzierung, Timing) und **`references/components.md`** (alle Bausteine mit Parametern)
lesen. Dichte und erlaubte Elemente aus `profil.einblendungen`. Trigger-Zeiten mit
`python3 $SK/scripts/words.py "Phrase eins" "Phrase zwei"`. Texte nach `profil.schreibstil`.
Weniger ist mehr: lieber eine klare Textzeile als Label + Headline + Unterzeile.

### 7 · Bauen und kontrollieren – vor dem Rendern
`python3 $SK/scripts/build.py` (Freistellungen für Text-hinter-Person ~1 min pro 4 s), dann
`cd segs/<id> && npx hyperframes lint .` für ein paar Segmente (0 Fehler; Warnungen zu doppelter Videoquelle sind
gewollt) und `python3 $SK/scripts/qa.py` → `qa/sheet_*.jpg` **ansehen**. Prüfen: Kamera/Gesicht frei, Text lesbar
(auch über hellen Webseiten, sonst Position ändern), höchstens zwei Headline-Zeilen, nichts abgeschnitten,
Abo-Animation sitzt. Korrigieren, `build.py <id>` + `qa.py <id>`.

**Pflicht vor dem Rendern: Positionsprüfung.** `python3 $SK/scripts/check_layout.py` misst jede Einblendung im echten
Browser-Layout und meldet **RAND** (ragt über den Bildrand) und **GESICHT** (liegt vor dem Gesicht; im Vollbild um
`layout.face`, im Split im oberen Teil der Kamera). Muss mit „OK – keine Probleme“ enden. Ausnahme ist nur der gewollte
Rahmen-Look (Learning/Kapitel mit der Person scharf im 9:16-Rahmen). Häufigste Ursache: Position nach dem Layout des
ERSTEN Moments gewählt, kurz danach wechselt das Bild (Split ↔ Vollbild). Position immer nach dem Layout wählen, das
im ganzen Zeitfenster überwiegt; große Einblendungen im Vollbild unten oder seitlich, nie auf Augenhöhe. Nach jeder
Korrektur erneut prüfen und nur die geänderten Segmente neu bauen.

### 8 · Rendern
`bash $SK/scripts/render_all.sh` im Hintergrund: 3 Spuren × 4 Worker parallel (`HYPERFRAMES_RENDER_LOCK=off`,
`nice 10`, damit der Rechner bedienbar bleibt), längste Segmente zuerst, weniger Spuren bei knapper Platte, Lock
gegen Doppelstart, Nachlauf für Fehlschläge, prüft am Ende jede Datei auf volle Frame-Zahl. ~2× Echtzeit der
Segmentlängen auf einem schnellen Mac. Weniger Kerne/RAM oder nebenher arbeiten: `RENDER_LANES=1 bash …` (oder 2). Wird ein Lauf abgebrochen, **erst prüfen, dass kein
Render-Prozess mehr läuft** (`ps aux | grep "hyperframes render"`).
Korrekturen später: betroffene `renders/<id>.mp4` wegräumen, `build.py <id>`, `render_all.sh` (überspringt fertige), assemble.

### 9 · Musik (parallel zu 8, nur wenn `ton.musik`)
Musikfenster festlegen (`references/audio.md`), dann:
`~/.cache/youtube-videoschnitt/mgenv/bin/python $SK/scripts/music.py intro=130 work=140 reveal=110 outro=130`
(Sekunden = längstes Fenster der Stimmung + Puffer). Aussetzer werden automatisch herausgeschnitten.

### 10 · Mix
Fenster in `project.json → music` eintragen (**Quellzeit** – mix.py rechnet selbst mit `S()` um), dann
`~/.cache/youtube-videoschnitt/mgenv/bin/python $SK/scripts/mix.py`. Kontrolle: Musik 13–18 LU unter der Stimme.

### 11 · Zusammenbau
`~/.cache/youtube-videoschnitt/mgenv/bin/python $SK/scripts/assemble.py "../<ablage.ergebnis>"` (~10–15 min; die
Python-Umgebung enthält Pillow für das Werbung-Label). Danach Stichproben: Kontaktbogen der fertigen
Datei (ein Bild pro Minute), Lautheit, Dauer = Schnittlänge + Endkarte.

### 12 · Kapitel, Transkript und Übergabe
`python3 $SK/scripts/export_texts.py` → `../<ablage.transkript_datei>`. Kapitel festlegen (Quellzeiten der
Abschnittsanfänge, mit `S()` umgerechnet; erstes Kapitel `0:00`, jedes ≥ 10 s) und als `../<ablage.kapitel_datei>`
ablegen (`references/description.md`). Kurz berichten: Ergebnisdatei, Länge vorher/nachher, was eingebaut wurde,
was die Person selbst prüfen sollte (Ton anhören – Musik ist KI-generiert), Größe des Arbeitsordners (Aufräumen
anbieten). Nach Feedback fragen und es ins Profil übernehmen.

### 12b · Shorts (wenn gewünscht oder `profil.shorts` an)
3–5 starke Momente (20–60 s, in sich verständlich, Pointe/Aha am Ende) aus dem geschnittenen Transkript wählen, mit
Hook-Titel als `shorts.json` anlegen (Format im Kopf von `scripts/shorts.py`), dann
`python3 $SK/scripts/shorts.py --vorschau` (Kontrollbilder: Gesicht im Ausschnitt? sonst `face_x`), danach ohne
`--vorschau` → `../Shorts/<name>.mp4` (1080×1920, Untertitel Wort für Wort, −14 LUFS).

### 13 · Optional: Timeline für DaVinci Resolve
Nur wenn die Person von Hand nachjustieren will. `python3 $SK/scripts/export_resolve.py` (~30 s) → `resolve/<Titel>.xml`
plus Originalton und Soundeffekte als WAV in `resolve/`. In Resolve: neues Projekt, Datei → Importieren → Timeline
(geht auch in der Gratisversion). Spuren: V1 Schnitt mit Reserve an jedem Clip, V2 Kamera-Einschübe, V3 fertige
Grafik-Blöcke (deckend, zum Schneiden ausschalten), A1 Originalton verlinkt, A2 Musik, ab A3 Soundeffekte, letzte Spur
gemasterte Stimme (aus, Referenz), Kapitel als Marker. Grenze: Werden Schnitte auf V1 geändert, passen die
Grafik-Blöcke auf V3 nicht mehr mit.

## Wenn etwas hakt
`references/pitfalls.md` sammelt die Fallstricke aus echten Produktionen (Lint-Regeln, Render-Kollisionen,
Encoder-Bitrate, Freistellung, Musik-Aussetzer, Kamera-Sync). Erst dort nachsehen.
