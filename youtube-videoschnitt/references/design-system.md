# Designsystem für Video-Einblendungen

Die konkreten Werte (Farben, Schrift) stehen im Profil (`profil.json → marke`). lib.py setzt sie als CSS-Variablen.
Diese Datei erklärt die Regeln, damit neue Bausteine (`raw()`) im selben Stil entstehen.
Nach jeder Änderung am Profil: `setup_profil.py`, dann `vorschau.py` ansehen.

## Grundsatz: clean statt KI-Look
Einblendungen sehen aus wie in einem gut geschnittenen Film, nicht wie eine App-Oberfläche: freier Text mit weichem
Schatten, ruhige Bewegung, viel Luft. Entstanden ist der Stil aus echtem Feedback zu einer früheren Fassung mit
Glaskacheln, 3D-Icons und zwei Schriften: „sieht zu sehr nach KI aus“. Seitdem gilt:

- **Eine Schrift**, Text direkt im Bild, kaum Flächen.
- Keine Glaskacheln, keine Icons neben Text, keine Kicker in Großbuchstaben mit Punkt davor, keine Pillen für normale Aussagen.
- Flächen nur dort, wo etwas wirklich ein Objekt ist: Screenshot im Browserrahmen, Suchleiste, Abo-Button, CTA-Pille,
  Partner-Einblendung.

## Typografie: nur die Profilschrift (`marke.schriften.text`, Standard Poppins)
| Rolle | Klasse | Schnitt | Laufweite | Größe (1920×1080) |
|---|---|---|---|---|
| Headline | `.hl` | 600 | **−0,04 em** | 54–104 px (Name 52, Learning 84, Kapitel 104) |
| Listenpunkte, Begriffe, kurze Hinweise | `.li` | 600 | −0,025 em | 36–40 px |
| Fließtext, Unterzeilen | `.tx` | 400 | −0,01 em | 28–32 px |
| Label über der Headline | `.lbl` | 600, 70 % Deckkraft | −0,01 em | 25 px, normale Schreibweise |
| Text hinter der Person | `.tb` | 600 | −0,04 em | 260–300 px |

- **Akzent** `*wort*`: In Headlines steht das Akzentwort voll hell, der Rest der Headline bei 62 %. Das ruhige
  „grau → weiß“-Prinzip. In Fließtext und Listen wird das Akzentwort Semibold. Höchstens ein Akzent pro Zeile.
- Labels sind optional. Nur setzen, wenn sie Information tragen („Prompt 2“, „Learning #1“), sonst `''`.
- Mindestgrößen: nichts unter 25 px; frei stehender Text braucht mehr Größe als Text auf einer Fläche.
- Die Klasse `.serif` gibt es nur noch als wirkungslosen Alias, damit ältere Storyboards nicht brechen.

## Lesbarkeit ohne Kachel
- Jeder Textblock hat einen **weichen Schatten** dahinter (`.sc`): radialer Verlauf in `basis`, zusätzlich 60 px
  weichgezeichnet, reicht ~100–130 px über den Text hinaus. Dazu `text-shadow` auf jeder Zeile (`.sh`). Nicht enger
  oder dunkler machen, sonst wirkt es wieder wie eine Kachel.
- Im **Bildschirm-/Split-Teil** (fremder Text, helle Webseiten dahinter) zusätzlich ein weit auslaufender Blur mit
  leichter Abdunklung (`.sb`, automatisch; `blur=False` schaltet ihn ab). Deckkraft dort 0,5, im Talking Head 0,3
  (`shade=` überschreibt).
- Reicht das nicht (z. B. weißer Dialog direkt hinter dem Text), erst die Position ändern; nur im Notfall `box=True`:
  schlichte dunkle Fläche ohne Kante und ohne Icon (`.pn`).

## Farb-Tokens (CSS-Variablen)
| Token | Variable | Einsatz |
|---|---|---|
| papier | `--papier` | aller Text im Bild |
| basis / basis2 | `--basis` / `--basis2` | Schatten hinter Text, Abdunklungen, Endkarte (müssen dunkel sein) |
| tinte | `--tinte` | Text auf hellen Pillen (Abo-Button, CTA-Pille) |
| marke1–3 | `--marke1` … `--marke3` | Balken in `compare`, Diagramme, Initialen-Kreis, Werbung-Label |
| akzent | `--akzent` | **nur** CTA-Pille „Link in der Beschreibung“ und Abo-Zustand „Abonniert“ |
| grau / sand | `--grau` / `--sand` | Nebeninfos, Platzhalter |

In Python stehen die Werte als `F['akzent']` (Hex) und `RGB['akzent']` (`"r,g,b"` für `rgba()`) bereit.
Keine knalligen Farben, keine Verläufe auf Text, kein YouTube-Rot (auch der Abo-Button ist Tinte → Akzent).
Ältere Variablennamen (`--ink`, `--cream`, `--aqua`, `--lime` …) sind Aliase auf die Tokens oben.

## Bewegung: ruhig, filmisch
- **Einstieg Text:** Label blendet auf, dann steigen die Headline-Wörter einzeln ein (y 22 → 0, Unschärfe 10 px → 0,
  0,85 s, `power3.out`, 55 ms Versatz), Unterzeilen folgen. Listenpunkte erscheinen erst, wenn sie gesagt werden.
- **Ausstieg:** 0,5 s Ausblenden mit leichter Unschärfe, kein Wegfliegen.
- **Kapitel:** Kinobalken (2,39:1) fahren oben und unten ein, Bild wird abgedunkelt und geblurrt, großer Titel,
  feine Fortschrittslinie.
- **Text hinter der Person:** Buchstaben steigen weich mit Unschärfe ein, dann läuft das Wort **langsam** (Ziel
  200 px/s, Warnung über 240) einmal hinter dem Kopf durch. Kein Label darüber.
- Keine Pop-/Bounce-Effekte (`back.out`) bei Text. Sound-Effekte nur bei Kapiteln, Learnings, CTA, Abo-Störer,
  Text-hinter-Person und getippten Suchen, nicht bei jeder Texteinblendung.
- Nie `letterSpacing`, `width/height` oder Layout-Eigenschaften animieren (ruckelt, Lint-Fehler). Transform, Opacity,
  Filter.
- `backdrop-filter` nie in einem Element, dessen Eltern Opacity/Filter animieren (dann sieht der Blur nichts mehr).
  Deshalb animiert `_reveal` die Kinder (`.ct`, `.sc`, `.sb`) und nicht den Container.

## Raster
Ränder mindestens 96 px links/rechts, 80 px oben/unten. Text im Vollbild-Talking-Head links oder rechts neben dem
Kopf, linksbündig (rechts vom Kopf) bzw. `align='right'` (links vom Kopf), mit Abstand zum Gesicht (siehe
storyboard-guide.md). Wiederkehrende Elemente immer an derselben Stelle (z. B. alle Listen rechts auf Augenhöhe
minus 100 px), das wirkt ruhiger als jedes Mal neu platziert.

## Person im Rahmen
Wird die Person nachträglich im 9:16-Rahmen eingesetzt (Learning im Talking Head, Partner-Einblendung, eigene
raw-Bausteine), hat der Rahmen dieselbe Eckenrundung wie die eigene Kamera-Maske in der Aufnahmesoftware:
`aufnahme.rahmen_radius` im Profil als Anteil der Rahmenbreite (Standard 0,065). Keine Lichtkante, kein Rahmen,
nur weicher Schatten.

## Bilder, Logo, Kanalbild
Bilder nur, wenn sie wirklich etwas zeigen: Screenshots, generierte Fotos/Illustrationen, Mockups. Dann als echtes
Bild mit Rundung 16–18 px und Schatten, nicht in einer Kachel. Logo (`marke.logo_hell`) auf der Endkarte, Kanalbild
(`kanal.avatar`) im Abo-Störer. Keine Emojis als Gestaltungselement.
