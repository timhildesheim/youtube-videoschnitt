# Storyboard planen: was, wann, wo

## Dichte
**Weniger, dafür sauberer:** lieber eine klare Textzeile als eine Karte mit Label, Icon und Unterzeile. Nicht jeden
Gedanken einblenden, nur, was ohne Einblendung verloren ginge (Zahlen, Begriffe, Struktur).

Richtwert aus `profil.einblendungen.dichte_sekunden` (Standard: etwa alle 45 s eine Einblendung). Erfahrungswert aus
einem gut angekommenen 33-Minuten-Video: 47 Einblendungen in 35 Segmenten. Im Intro dichter (alle 5–10 s), in
langen Warte-/Demo-Passagen weniger. Lieber eine präzise Einblendung als drei generische.
Elemente, die im Profil abgeschaltet sind (`text_hinter_person`, `learnings`, `kapitelkarten`, `namens_bauchbinde`),
nicht verwenden.

## Was eingeblendet wird: aus dem Transkript ableiten
| Im Gesagten | Komponente |
|---|---|
| Hook-Satz mit Kernbegriff im Intro | `textbehind` (langsames Laufband, `t1=None`), optional `sub` |
| „In diesem Video …“ / Aufzählung des Ablaufs | `listcard`, Punkte als Text untereinander |
| Erstes Auftauchen der Person im Bild | `tile` als Namens-Bauchbinde (Label `profil.person.zusatz` oder `''`, Titel `profil.person.name` mit betontem Nachnamen, size 52) |
| Nennung von Tools, Techniken, Beispielen | `chips` (untereinander) |
| Jeder größere Abschnitt („Schritt 2 …“) | `chapter` (gleiche Gesamtzahl im ganzen Video) |
| Prompt wird diktiert / Anleitung | `listcard` „Prompt n · Thema“ mit den Kernforderungen als Punkte, die beim Aussprechen erscheinen |
| „Wichtig“, „Tipp“, „Merke“, ein Learning | `tile` mit Label „Tipp“, oder `learning` (2–4 pro Video, nur die stärksten) |
| Zahl, Vergleich, Aufwand | `compare` |
| Ergebnis-Liste auf dem Bildschirm | `zoom` darauf + `tag` |
| Erwähnung eines anderen Videos | `tile` „Video-Tipp“ |
| CTA aus dem Profil (Stichworte `cta.stichworte`) | `community` (groß), im Outro `outro_cta` |
| Ein Satz, der hängen bleiben soll | `quote` |
| Vorher/Nachher-Vergleich im Bild | `before_after` |
| Lustiger/menschlicher Moment | kleiner `tag` mit Augenzwinkern („Die KI arbeitet, du machst *Pause*“) |
| Bezahlte Kooperation (nur mit `sponsor` in project.json) | `sponsor` und `sponsor_link`, Regeln in `werbepartner.md` |

**Abo-Störer** (wenn `profil.abo_stoerer.aktiv`): einmal nach dem Hook/der Roadmap (ca. 0:45–2:00) an einer Stelle
ohne andere Einblendung, bei `anzahl: 2` ein zweites Mal bei etwa 60 %. Spricht die Person selbst übers Abonnieren,
genau dort.

## Texte
- Kurz und konkret, in der Videosprache, nach `profil.schreibstil.regeln`. Label nur, wenn es Information trägt
  („Prompt 2“, „Tipp“), sonst `''`. Label + Headline + Unterzeile + Icon ist genau der Kachel-Look, der nach KI aussieht.
- Ein Akzentwort pro Headline: das Wort mit der Bedeutung („Erst *anrufen*, dann bauen“). Es steht hell, der Rest
  leicht zurückgenommen. Nur die Profilschrift, keine zweite Schrift.
- Headlines höchstens zwei Zeilen, Listenpunkte höchstens eine Zeile (sonst kürzen, nicht kleiner setzen).
- Fakten nur aus dem Gesagten oder dem Bild. Modellnamen/Zahlen, die man nicht sicher hört, weglassen.
- Eigennamen aus dem Bild prüfen (Whisper schreibt z. B. „Versal“ statt Vercel, „GCEP“ statt GSAP, „School“ statt Skool).

## Timing
- Einblendung erscheint **mit** dem Stichwort (Whisper-Zeit des ersten Worts, ±0,3 s ist ok), nicht danach.
- Standzeit mindestens 4 s, Listen so lange, bis der letzte Punkt gesagt ist + 3 s.
- Text-hinter-Person (Laufband) läuft langsam (200 px/s): `t1=None` rechnet das Fenster aus (≈ 8–12 s je nach
  Wortlänge). Kurze Wörter wählen (≤ 10 Buchstaben), damit es nicht ewig läuft. Danach erst die nächste Einblendung
  auf der linken Seite (dort endet das Wort). Learnings 8–10 s, Kapitel 5–6 s, Abo-Störer ~6 s.
- Keine zwei großen Einblendungen gleichzeitig. Tags dürfen parallel zu Listen laufen, wenn sie sich nicht berühren.

## Platzierung
Vorher die freien Flächen des Layouts bestimmen (`references/layouts.md`). Grundsätze:
- Kamera/Gesicht nie überdecken. Bei runder Facecam: unten rechts frei lassen (Kreis + 40 px Glow).
- Im Screen-Bereich über unwichtige Zonen legen: Seitenleisten, leere Chatflächen, Ränder. Nicht über das, worüber
  die Person gerade spricht (das Ergebnis, die Tabelle). Dann lieber zoomen.
- Im Vollbild-Talking-Head links oder rechts neben dem Kopf (die Person steht meist mittig), **mit Abstand**: Text
  links endet spätestens bei x ≈ 540 (`{'left':70}`, `w=460`, `align='right'`), Text rechts beginnt frühestens bei
  x ≈ 1380 (`{'left':1380}`, `w=460`). Der Push-in vergrößert das Gesicht bis 1,11×, der weiche Schatten hinter dem
  Text reicht ~130 px weiter. Listenpunkte dafür kürzer formulieren (≤ 22 Zeichen bei 34–38 px).
  `check_layout.py` sperrt ±390 px um die Gesichtsmitte.
- Große Einblendungen im Vollbild unten oder seitlich, nie auf Augenhöhe. Position immer nach dem Layout wählen, das im
  ganzen Zeitfenster der Einblendung überwiegt (kurz danach kann das Bild von Split auf Vollbild wechseln).
- Tags oben mittig, Abo-Störer unten links (bei Split-Layout über dem Bildschirmbereich unten).
- Nach jeder Änderung `qa.py` und `check_layout.py`. Die Bilder sind der Maßstab, nicht die Annahme.
