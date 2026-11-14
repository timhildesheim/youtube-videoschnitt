# Bilder und Screenshots

Welches Werkzeug genutzt wird, steht in `profil.bilder.generator`. Andere Bilddienste nur nach Rückfrage.

## Screenshots (immer möglich)
`node $SK/scripts/shots.mjs <url> <name> [--full]` → `assets/<name>.jpg` (1440 CSS-px breit, DPR 2). Cookie-Banner:
es wird nur „Nur notwendige“/„Ablehnen“ geklickt. Braucht das von HyperFrames mitgebrachte Chrome
(`npx hyperframes doctor` einmal ausführen, falls es fehlt).

Bilder nur, wenn sie wirklich etwas zeigen (Screenshot, Foto, Mockup). Icons neben Text gibt es im Clean-Stil
bewusst nicht (`references/design-system.md`). Projektbezogene Bilder nach `<arbeitsordner>/assets/` legen,
build.py verlinkt sie automatisch in jedes Segment.

## Ohne Bildgenerator (`generator: keiner`)
Für plakative Momente Screenshots, Zahlen (`compare`, eigene Zähler mit `raw()`), Zitate oder Text-hinter-Person
einsetzen. Eigene Fotos der Person (z. B. aus einem Ordner, den sie nennt) dürfen genutzt werden.

## Mit Codex (`generator: codex`)
Die Codex-CLI steckt in der ChatGPT-Desktop-App und nutzt das ChatGPT-Abo – kein API-Key nötig. Pfad:
`profil.bilder.codex_pfad`, sonst `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`
(ändert sich mit App-Updates; suchen mit `find /Applications/ChatGPT.app -name codex -type f`). Ein Lauf dauert
1–2 min, mehrere parallel im Hintergrund starten.

Editorial-Foto 3:2 (Hook, Kapitelstarts, Ziel/Ergebnis), im Arbeitsordner unter `assets/`:
```bash
CODEX="<pfad>"
cd "<Videoordner>/<arbeitsordner>/assets"
$CODEX exec --skip-git-repo-check --sandbox workspace-write "Generate one image using your image generation tool: <MOTIV>, <profil.bilder.foto_stil> No people. Save it as hero_<name>.jpg in the current directory." > log_<name>.txt 2>&1 &
```
Freigestellte Objekte für Animationen (z. B. fallende Scheine, Objekte, die ins Bild fliegen): „isolated on a fully
transparent background (PNG with alpha)“ in den Prompt, „make sure it has a real alpha channel“ ans Ende.
Echte Geldscheine, Logos fremder Marken und reale Personen nie nachbilden lassen.

Gelungene Motive, die wieder vorkommen (Serien, wiederkehrende Themen), in den Profilordner kopieren
(Unterordner `bilder/`) und in `profil.wuensche` vermerken. Gezeigt werden sie als echtes Bild mit Rundung 16–18 px
und Schatten (`raw()`), nicht in einer Kachel.

## Anderes Werkzeug (`generator: anderer`)
Vorgehen steht in `profil.bilder.hinweis`. Gleiche Regeln: keine Schrift im Bild, Palette aus
`profil.marke.farben`, transparente PNGs nur für freigestellte Objekte.
