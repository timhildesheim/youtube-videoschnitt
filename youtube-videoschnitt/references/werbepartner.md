# Bezahlte Werbepartnerschaften im Video

Ist ein Video eine bezahlte Kooperation, braucht es nur `"sponsor": "<partner>"` in `project.json` und die passenden
Stellen im Storyboard. Logo, Farbe, Rabattcode und Link liegen einmalig im Profil.

## Partnerdaten
Jeder Partner hat einen Ordner `~/.config/youtube-videoschnitt/partner/<name>/` mit Logos (PNG mit Transparenz) und
`partner.json`:

```json
{
 "name": "Beispiel Hosting",
 "color": "#5b3fd6",
 "color_soft": "#f3f0fd",
 "logo": "logo.png",
 "icon": "icon.png",
 "code": "MEINCODE10",
 "discount": "10 %",
 "url": "https://partner.example/?ref=meincode",
 "url_display": "partner.example/meincode",
 "headline": "",
 "code_label": "",
 "applied": "",
 "footer": "",
 "notes": "Vertragskern, Ansprechpartner (nur zur Info, wird nicht eingeblendet)"
}
```

| Feld | Bedeutung |
|---|---|
| `name`, `color`, `color_soft` | Markenname, Markenfarbe, helle Feldfarbe für das Gutscheinfeld |
| `logo`, `icon` | Dateinamen im Ordner (build.py verlinkt alle Bilder des Partners in jedes Segment) |
| `code`, `discount` | eigener Rabattcode und Rabatt |
| `url`, `url_display` | Tracking-Link und die Kurzform für die Einblendung |
| `headline`, `code_label`, `applied`, `footer` | eigene Texte der großen Einblendung; leer = Standard aus `profil.texte` (`rabatt`, `rabattcode`, `code_angewendet`, `link_und_code`) |

`project.json` kann einzelne Felder pro Video überschreiben: `"sponsor": {"partner": "<name>", "code": "…"}`.

## Bausteine (lib.py)
| Methode | Wofür |
|---|---|
| `c.sponsor(id, t0, t1, type_at=None, headline=None, mode=None)` | Große, plakative Einblendung: weiße Fläche, Partner-Logo, Headline mit Akzent in Markenfarbe, Rabattcode wird groß in ein Gutscheinfeld getippt (blinkender Cursor), danach Pille „Code angewendet ✓“, darunter Link + „Link und Code in der Beschreibung“. `mode='panel'` (Standard im Split): weiße Fläche exakt über dem Bildschirmbereich, Kamera bleibt. `mode='full'` (Standard im Vollbild): weißer Vollbild-Hintergrund, die Person scharf im 9:16-Rahmen links. Standzeit 8–12 s. `type_at` = wenn der Code ausgesprochen wird. |
| `c.sponsor_link(id, t0, t1, type_at=None)` | Kleine weiße Pille mit Partner-Icon, getipptem Link und Pfeil „Link in der Beschreibung“. Für „ich blende dir den Link ein“. Split: unten mittig im Bildschirm, Vollbild: unten links. |

Sound: whoosh beim Einstieg, Tippgeräusch, Pop bei „Code angewendet“.

## Werbekennzeichnung
`assemble.py` legt automatisch das Wort aus `profil.texte.werbung` oben rechts ins Bild, sobald `project.json` einen
`sponsor` hat (abschalten: `"ad_label": false`, anderer Text: `"ad_label": "Anzeige"`). Stil: nur das Wort,
Textschrift 500, Farbe `marke3` mit 30 % Deckkraft, in 4K 54 px groß, 48 px vom rechten und 40 px vom oberen Rand.

Empfehlung: das Label **nur in den Abschnitten**, in denen über den Partner gesprochen wird. Dafür
`"ad_label_ranges": [[von, bis], …]` in Quellzeit eintragen (wie im Storyboard; assemble rechnet über die
Schnittliste um). Ohne `ad_label_ranges` läuft das Label durchgehend, das passt, wenn der Partner das ganze Video
trägt. Ob 30 % Deckkraft als „gut lesbar“ gilt, ist eine Abwägung (in Deutschland: Vorgaben der
Landesmedienanstalten). Mehr Deckkraft ist sicherer. Zusätzlich in YouTube „Enthält bezahlte Werbung“ anhaken.

## Wo die Einblendungen hingehören
Aus der Praxis:
1. **Partner-Einstieg** („XY ist Partner dieses Videos“): noch keine große Einblendung, das wirkt zu früh. Den Partner
   erst mit Text und Listen vorstellen.
2. **Link**, wenn er genannt oder eingetippt wird: `sponsor_link`.
3. **Checkout**: Viele Partner verlangen, dass der Weg bis zum Checkout samt Einlösen des Codes im Bild zu sehen ist.
   Die echte Code-Eingabe auf dem Bildschirm deshalb NICHT überdecken, die große Einblendung direkt danach setzen
   (wenn der Preis mit Code steht). Preise aus dem Bild nehmen, nicht aus dem Gesagten (man verspricht sich leicht).
4. **Outro**, wenn der Code noch einmal genannt wird: eine große Einblendung. Wird der Partner kurz danach erneut
   genannt, dort keine zweite.

Faustregel: zwei große Einblendungen pro Video (direkt nach dem Checkout und im Outro), dazu die Link-Pille.
Zwischen zwei Partner-Einblendungen andere Inhalte (Abo-Störer, CTA), nie zwei weiße Flächen direkt hintereinander.

## Checkliste für den Partner-Brief
- Partnername korrekt aussprechen, Code mündlich nennen und einblenden, Checkout bis zum Einlösen zeigen, klarer CTA.
- Tracking-Link und Code ganz oben in die Beschreibung (ohne Aufklappen sichtbar), dazu ein angepinnter Kommentar.
- Abnahmen des Partners (Skript, ungelisteter Entwurf) rechtzeitig vor der Veröffentlichung einplanen.
- YouTube-Haken „Enthält bezahlte Werbung“ setzen.
