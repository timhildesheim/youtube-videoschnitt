# Layouts erkennen und in project.json eintragen

Koordinaten immer in CSS-px des 1920×1080-Rasters (= 4K-Pixel / 2). Bekannte Setups des Kanals stehen in
`profil.aufnahme.setups` (beim Einrichten oder beim ersten Video vermessen) – prepare.py belegt `layout` mit dem
ersten davon vor. Trotzdem jedes Video prüfen; ein neues Setup vermessen und ins Profil übernehmen
(`{"name": "…", "beschreibung": "…", "layout": {…}}`).

## Typische Setups
**A · Vollbild-Talking-Head + Bildschirm mit runder Facecam**
```json
"layout": {"type": "circle-cam", "face": [0.494, 0.40],
           "cam": {"shape": "circle", "cx": 1685.5, "cy": 851, "r": 168, "glow": 40},
           "screen": {"x": 0, "y": 0, "w": 1920, "h": 1080}}
```
**B · Kamera als 9:16-Fenster neben dem Bildschirm (Split), Hintergrundbild**
```json
"layout": {"type": "split", "face": [0.5, 0.4],
           "cam": {"shape": "rect", "x": 50, "y": 60, "w": 540, "h": 960, "radius": 24},
           "screen": {"x": 640, "y": 190, "w": 1230, "h": 692}}
```
**C · Nur Bildschirm** – `"type": "fullscreen", "cam": null, "screen": {"x":0,"y":0,"w":1920,"h":1080}`.

Werte sind Beispiele – **immer vermessen**. Ob es daneben Vollbild-Talking-Head-Passagen gibt, aus den
Kontaktbögen ablesen. Im Split-Layout: Karten über den Bildschirmbereich oder den Hintergrund legen, nie über die
Kamera; `textbehind` nur in Vollbild-Talking-Head-Abschnitten; Zooms bleiben automatisch im Bildschirmbereich.

## Vermessen
1. Frame als Rohdaten holen: `ffmpeg -ss <t> -i base.mp4 -frames:v 1 -vf scale=1920:1080 -f rawvideo -pix_fmt rgb24 f.raw`
2. Kreis: Pixel eines farbigen Rings (z. B. `b>170 & g>160 & r<140` für Cyan) sammeln → Mittelpunkt = Mittelwert,
   Radius = Median des Abstands. Ohne Ring: Kante über Helligkeitssprung entlang mehrerer Strahlen.
3. Rechteck: Kanten über Helligkeits-/Farbsprünge entlang einer Zeile und Spalte bestimmen, oder ein Gitterbild
   (`drawgrid=w=160:h=90`) ansehen und auf 5 px genau ablesen. Eckenradius an der Rundung ablesen (oder aus der
   Masken-PNG der Aufnahmesoftware: Alpha-Kante vermessen, durch 2 teilen) – damit die scharf gehaltene Kamera beim
   Vollbild-Blur genau dieselbe Rundung hat.
4. Gesicht im Vollbild-Talking-Head: Gitterbild ansehen, Mitte zwischen den Augen als Anteil der Breite/Höhe.

## Talking-Head-Grenzen frame-genau
`frames/scenes.txt` liefert Kandidaten (Keyframes, ±2 s). Danach mit 30-fps-Thumbnails im Fenster ±4 s die exakte
Frame-Grenze bestimmen (Signatur z. B. mittlere Farbe des linken Rands oder der Kamerafläche) und in
`talking_head_ranges` eintragen. Kurze Ausreißer (einzelne Keyframes, App-Wechsel) sind kein Talking Head – mit einem
Einzelbild gegenprüfen.

## Bildschirminhalt zeitlich analysieren
Für `before_after` oder Zooms: 10-fps-Thumbnails einer Region auswerten (z. B. Kopfbereich hell = neue Seite,
farbig = alte Seite) und die Umschaltzeiten automatisch bestimmen; Blitzer < 0,4 s ignorieren.

## Erprobte Positionen im Split-Layout (Kamera links)
Community-Einblendung: `text_pos={'left':660,'top':110}, tw=560, browser_pos={'left':1250,'top':230}, bw=620`.
Abo-Störer: `subscribe_pos={'left':660,'top':920}` (unter dem Bildschirm). Learning/Kapitel weichen der Kamera
automatisch aus, die Kamera bleibt bei Vollbild-Blur scharf.

## Separate Kameraspur (Vollbild-Kamera-Einschübe)
Manche Setups nehmen zusätzlich die Kamera als eigene Datei auf (oft mit stummer Tonspur und minimal anderem Start).
Synchronisation per `sync_cam.py` (Bewegungsverlauf, Kreuzkorrelation, siehe SKILL.md Schritt 2b). Erfahrungswerte:
gleicher Versatz an allen Messstellen (z. B. konstant −2 Frames), Korrelation ~0,78 am Maximum gegenüber ~0,45 einen
Frame daneben (framegenau).
Bildausschnitt: Die Rohkamera ist meist weiter als die Vollbild-Kamera-Szene im Hauptvideo (die Aufnahmesoftware
zoomt hinein). `match_crop.py` misst das (FFT-Kreuzkorrelation Rohkamera ↔ Vollbild, Übereinstimmung > 0,99 =
deckungsgleich), render_base.py setzt die Kamera dann mit genau diesem Ausschnitt ein. Den Wert in
`profil.aufnahme.kamera_spur.crop` speichern; ändert sich die Szene, neu messen.
