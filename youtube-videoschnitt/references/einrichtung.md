# Einrichtungsinterview

Läuft beim **ersten Einsatz** (kein `~/.config/youtube-videoschnitt/profil.json`) und immer, wenn die Person
„Skill einrichten“, „neu einrichten“ oder „Profil ändern“ sagt. Ziel: ein vollständiges Profil, mit dem jedes
Video ohne weitere Rückfragen im Stil des Kanals geschnitten wird. Dauer 10–15 Minuten.

## Grundsätze
- Kurz erklären, was passiert: „Ich stelle dir in 8 kurzen Blöcken Fragen zu Kanal, Marke, Aufnahme und Stil.
  Alles lässt sich später ändern. Am Ende siehst du eine Vorschau der Einblendungen in deinen Farben.“
- **Parallel** zum Interview `bash $SK/scripts/check_env.sh` im Hintergrund starten (richtet Python-Umgebung,
  Whisper-Modell usw. ein, dauert beim ersten Mal 5–15 min). Fehlende Werkzeuge erst am Ende ansprechen.
- Pro Block **ein** Aufruf des Frage-Werkzeugs (AskUserQuestion, bis zu 4 Fragen, Empfehlung zuerst). Gibt es das
  Werkzeug nicht, höchstens 3–4 Fragen pro Nachricht als nummerierte Liste.
- Alles selbst herausfinden, was man herausfinden kann (Kanalname, Kanalbild, Farben und Schriften der Website),
  und **zur Bestätigung vorschlagen** statt danach zu fragen.
- Antworten sofort in einen Entwurf `profil.json` schreiben (Struktur: `$SK/profil-vorlage/profil.json`, Kommentare
  dort erklären jedes Feld). Profilordner: `~/.config/youtube-videoschnitt/` (oder `$YTV_PROFIL`).
- Keine Passwörter, Zugangsdaten oder API-Keys abfragen oder speichern.

## Block 1 · Kanal und Person
1. Link zum YouTube-Kanal (z. B. `https://www.youtube.com/@name`) → daraus `kanal.url`. Seite laden (curl mit
   `-H 'Cookie: SOCS=CAI'`) und Kanalname (`og:title`) und Handle (`@…` aus der URL) übernehmen; Kanalbild holt später
   `setup_profil.py --avatar-von-kanal`. Ohne Kanal: Name und Handle erfragen.
2. Name der Person im Video (Namens-Bauchbinde) und Zusatz darüber (Marke, Rolle oder nichts).
3. Sprache der Videos (`sprache`, steuert Transkription und Beschriftungen). Bei Englisch die `texte` übersetzen
   (Subscribe/Subscribed, Step {n} of {total}, Learning #{n}, Before/After, “ ”, Link in the description, Ad …).

## Block 2 · Marke und Design
1. Gibt es eine Website oder ein Designsystem? Wenn ja: Seite laden (Firecrawl/Browser/curl), Farben aus CSS-Variablen
   und häufigsten Farbwerten ablesen, Schriften aus `font-family`/Google-Fonts-Links. Daraus die zehn Tokens
   vorschlagen (Rollen siehe `references/design-system.md`). Wichtig: `basis` muss dunkel sein (Schatten hinter
   Text, Abdunklungen), `papier` hell (aller Text im Bild), `akzent` eine auffällige Farbe für die CTA-Pille, die
   **nur sparsam** eingesetzt wird.
2. Ohne Marke eine der Paletten anbieten (Werte in `profil.marke.farben` übernehmen):
   | Palette | basis | basis2 | tinte | papier | marke1 | marke2 | marke3 | akzent | grau | sand |
   |---|---|---|---|---|---|---|---|---|---|---|
   | Graphit & Gelb (Standard) | #15171c | #23272f | #1c1c1f | #f6f5f2 | #26456d | #3d72b3 | #9cc6ff | #ffd54f | #8b8f98 | #d8d4cc |
   | Mitternacht & Koralle | #141a2a | #222b40 | #1a1d26 | #f7f6f2 | #23406e | #3e6fb8 | #a9c8f5 | #ff8a65 | #8a90a0 | #d9d5cd |
   | Bordeaux & Sand | #1e1416 | #2e2022 | #221a1b | #faf5f0 | #6b2333 | #a3384f | #e8a3b0 | #f2c48d | #94898a | #ddd2c6 |
   | Violett & Apricot | #1a1423 | #2a2138 | #1b1720 | #fbf8ff | #4b2a7a | #7b4bd1 | #c9b2ff | #ff9f68 | #8d8698 | #ddd6e6 |
3. Schrift: **eine** Schrift für alle Einblendungen (klar, gut lesbar, mit Schnitten 400 und 600). Kurz erklären,
   warum nur eine: Mehrere Schriften und Kacheln lassen Einblendungen schnell nach KI aussehen, eine Schrift mit
   hellem Akzentwort wirkt ruhig und hochwertig. Google-Fonts-Name genügt. Eigene Schriftdateien (TTF/OTF) kann die
   Person in `~/.config/youtube-videoschnitt/fonts/` legen. Standard: Poppins.
4. Logo für die Endkarte: Pfad zu einer hellen/weißen Version (PNG mit Transparenz) → in den Profilordner als
   `logo-hell.png` kopieren. Optional, ohne Logo zeigt die Endkarte nur Text.

## Block 3 · Call-to-Action und Abo-Störer
1. Was soll das Video bewerben? Community (Skool, Discord …), Newsletter, Kurs/Produkt, Website, nichts.
   Bei „nichts“: `cta.aktiv = false` (Endkarte zeigt dann den Kanal und „Abonnieren“).
2. Link (`cta.url`), Kurzanzeige für die Browserleiste (`cta.anzeige`), Label (`cta.label`, z. B. „Kostenlose
   Community“), Titel der Einblendung (`cta.titel`, ein Wort mit `*…*` betont), Text der Pille (`cta.pille`).
3. Endkarte: Claim (`cta.claim`, ein Satz mit einem betonten Wort) und Unterzeile (`cta.endkarte_sub`).
4. Abo-Störer (animierte „Abonnieren + Glocke“-Pille): in jedem Video? Einmal oder zweimal? Woran erkennt man im
   Gesagten, dass der CTA erwähnt wird (`cta.stichworte`, z. B. „Community“, „Newsletter“, „Link in der Beschreibung“)?

## Block 4 · Aufnahme-Setup
1. Womit wird aufgenommen (OBS, Screen Studio, Kamera allein, Riverside …) und in welcher Auflösung?
2. Welche Bildaufteilungen kommen vor (Mehrfachauswahl): Vollbild-Kamera (Talking Head) · Bildschirm mit runder
   Facecam · Kamera-Fenster neben dem Bildschirm (Split) · nur Bildschirm.
3. Gibt es eine **separate Kameraspur** (eigene Datei, nur Kamera, gleiche Aufnahme)? Wie heißt sie typischerweise
   (`aufnahme.kamera_spur.erkennung`)? Dann sind Vollbild-Kamera-Einschübe möglich.
4. Bitte um eine **Beispielaufnahme** (Pfad). Wenn vorhanden: wie in `references/layouts.md` Kontaktbogen erzeugen,
   die Setups vermessen (Kamera-Position/-Form, Bildschirmbereich, Gesichtsmitte) und als `aufnahme.setups` speichern,
   jeweils mit Namen und Beschreibung. Ein Standbild davon dient später als Hintergrund der Vorschau.
   Ohne Beispiel: Setups leer lassen, sie werden beim ersten Video vermessen und dann ins Profil übernommen.
5. Hat die Kamera in OBS (o. Ä.) abgerundete Ecken? Dann `aufnahme.rahmen_radius` so setzen, dass Einblendungen mit
   der Person im 9:16-Rahmen dieselbe Rundung haben (Radius ÷ Breite der Maske, z. B. 140 px ÷ 2160 px = 0,065).

## Block 5 · Ablage
1. Wo liegen die Videos? (`ablage.wurzel`, z. B. `~/Movies/YouTube/Videos`) Ein Unterordner pro Video?
   Benennungsschema (`ablage.ordner_schema`)?
2. Name des fertigen Videos (`ablage.ergebnis`, Platzhalter `{name}` = Name des Originals) und des Arbeitsordners.
3. Legen andere Werkzeuge Dateien in denselben Ordner (Beschreibung, Thumbnails, Social-Posts)? Diese als
   `ablage.geschuetzt` eintragen, sie werden nie überschrieben. Gibt es eine Beschreibungsdatei mit Kapiteln
   (`ablage.beschreibung_datei`)? Gibt es einen Skill dafür (`begleit_skill`)?

## Block 6 · Schnitt und Einblendungen
1. Schnitt: nur Pausen, Versprecher und Wiederholungen raus (empfohlen, `schnitt.inhalt_kuerzen = false`) oder auch
   inhaltlich straffen?
2. Dichte der Einblendungen: zurückhaltend (alle ~90 s) · mittel (alle ~45 s, empfohlen) · dicht (alle ~25 s).
3. Welche Elemente (Mehrfachauswahl): großes Wort hinter der Person · Learning-Karten · Kapitelkarten ·
   Namens-Bauchbinde. Push-in-Zooms an Schnitten: dezent (1,06) · mittel (1,11, empfohlen) · aus (1,0).
4. Schreibstil für Texte und Kapitel: Du/Sie, Emojis ja/nein, sonstige Regeln (→ `schreibstil.regeln`).

## Block 7 · Ton
1. Stimme: im Original lassen (empfohlen, `ton.stimme_fx = "anull"`) oder veredeln? Eine Kette nur nach einer
   lautheitsangeglichenen Hörprobe beim ersten Video festlegen (`references/audio.md`).
2. Musik: nur in passenden Szenen (Intro, Arbeitsphasen, Ergebnis, Outro – empfohlen) · gar nicht. Gewünschte
   Stilrichtung? (→ eigene Prompts in `ton.musik_stimmungen`, Vorlagen in `scripts/music.py`)
3. Sound-Effekte: dezent (empfohlen) · gar nicht. Ziel-Lautheit: −14 LUFS (YouTube) beibehalten?

## Block 8 · Bilder und Werbepartner
1. Gibt es einen Bildgenerator für eigene Fotos und Illustrationen (Hook, Kapitelstarts, Ziel/Ergebnis)?
   **Codex-CLI aus der ChatGPT-App** (mit ChatGPT-Abo, ohne API-Key, siehe `references/assets.md`) · ein anderes
   Werkzeug (in `bilder.hinweis` beschreiben) · keiner. Ohne Generator nur Screenshots. Icons gibt es im Clean-Stil
   bewusst nicht.
2. Gibt es bezahlte Kooperationen? Dann je Partner einen Ordner `~/.config/youtube-videoschnitt/partner/<name>/` mit
   `partner.json` und Logos anlegen (`references/werbepartner.md`). Kann auch später passieren.

## Abschluss
1. `profil.json` schreiben, dann
   `~/.cache/youtube-videoschnitt/mgenv/bin/python $SK/scripts/setup_profil.py --avatar-von-kanal`
   (Schriften laden, Kanalbild holen, Kontraste prüfen). Warnungen zu Kontrasten mit der Person klären.
2. `python3 $SK/scripts/vorschau.py [Standbild aus der Beispielaufnahme]` → `~/.config/youtube-videoschnitt/vorschau/vorschau.jpg`
   ansehen und der Person zeigen (Datei senden oder Pfad nennen). Nachbessern, bis es gefällt.
3. `python3 $SK/scripts/profil.py` muss „Alles da“ melden oder nur bewusst offene Punkte.
4. Kurze Zusammenfassung: was eingestellt ist, wie man es ändert („sag einfach: ändere im Videoschnitt-Profil …“),
   und dass Feedback nach jedem Video als Regel in `wuensche` landet, damit es beim nächsten Video gilt.

## Später ändern
Einzelne Werte direkt in `profil.json` anpassen (vorher lesen, nur das Gewünschte ändern), bei Farben/Schriften
danach `setup_profil.py` und `vorschau.py` erneut ausführen. Ein komplettes Neu-Einrichten sichert vorher
`profil.json` als `profil.vorher.json`.
