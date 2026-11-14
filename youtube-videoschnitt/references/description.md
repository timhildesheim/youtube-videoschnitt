# Kapitelmarken, Transkript und Beschreibung

Titel, Beschreibung und Thumbnails macht dieser Skill nicht (gibt es dafür einen eigenen Skill, steht er in
`profil.begleit_skill`). Er liefert, was dafür die Schnittzeiten braucht:

## Kapitelmarken (`profil.ablage.kapitel_datei`)
Nur die Kapitelzeilen, kopierfertig, Zeiten in **Schnittzeit** (`S(quellzeit)`):
```
0:00 Worum es geht
1:58 Schritt 1: Recherche
4:21 Das Ergebnis der Recherche
```
Regeln: erstes Kapitel `0:00`, mindestens 3 Kapitel, jedes ≥ 10 s (YouTube). Kapitel an den echten
Abschnittswechseln (dieselben wie die Kapitelkarten im Video, plus Intro, Ergebnis, Recap). Formulierung im Ton der
Person und nach `profil.schreibstil.regeln`; konkret statt Floskel.

## Geschnittenes Transkript (`profil.ablage.transkript_datei`)
`export_texts.py` – Grundlage für Beschreibung und Kapitel mit verlässlichen Zeitmarken.

## Vorhandene Beschreibung mit Kapiteln (`profil.ablage.beschreibung_datei`)
Wurde die Beschreibung vor dem Schnitt erstellt und enthält sie Kapitel, sind deren Zeiten falsch. Dann:
1. Kopie `<Datei> (vor Schnitt)` anlegen.
2. Nur den Kapitelblock durch den Inhalt der Kapitel-Datei ersetzen, den übrigen Text nicht anfassen.
3. Im Abschlussbericht darauf hinweisen.
Ohne Kapitel in der Beschreibung: nichts ändern, nur auf die Kapitel-Datei hinweisen.

Links für die Beschreibung: `profil.cta.url`, `profil.marke.website`.
