# Komponenten in lib.py

Alle Zeiten sind **Ausgabezeiten**. Im Storyboard immer über `S(quellzeit)` angeben. Positionen sind dicts in
CSS-px (`{'left':96,'top':170}`), Breiten `w` in px. Titeltexte unterstützen `*akzent*`.
Beschriftungen (Abonnieren, Schritt n von m, Learning #n, Vorher/Nachher, Link in der Beschreibung) kommen aus
`profil.texte`, Farben aus `profil.marke.farben` (`var(--akzent)`, `var(--marke3)` …). Stilregeln: `design-system.md`.

## Segmente
```python
c = comp('s07', 437.7, 452.4)          # Screen-/Split-Segment, Quellzeit von–bis
c = comp('th1', 0, 128.5, 'th')        # Vollbild-Talking-Head
c = comp('th9', 2124.8, 'end', 'th')   # bis zum Videoende
endcard()                              # 5-s-Endkarte, wird angehängt (immer als letztes)
```
Ein Segment = ein HyperFrames-Render mit dem Videoausschnitt als Hintergrund. Segmentgrenzen: erste Karte −0,3 s bis
letzte Karte +0,25 s. Karten mit < 1,5 s Abstand in ein Segment legen. Segmente dürfen keine Talking-Head/Screen-Grenze
überspannen und sich nicht überlappen. Vollbild-Talking-Head-Abschnitte immer komplett als ein `th`-Segment
(wegen der Push-ins), auch wenn dort wenige Karten sind.

## Kamera
| Methode | Wirkung |
|---|---|
| `c.th_pushins(wide_at=[(a,b),…], face=None)` | Pflicht in jedem `th`-Segment (auch Kamera-Einschübe, dann `face=CFG['camera']['face']`): an jedem Schnitt wechselnde Einstellung (weit/nah/halbnah) + langsamer Push, Stärke aus `schnitt.pushin_max`. In `wide_at`-Fenstern weit (für Text-hinter-Person). |
| `c.zoom(t0, t1, cx, cy, scale)` | Zoom auf Punkt (0..1 der Bildfläche) **nur im Bildschirmbereich** (`layout.screen`); Kamera bleibt unberührt, runde Facecam liegt scharf obendrauf. 1,5–1,8 für Tabellen/Text. Wird automatisch so begrenzt, dass keine Ränder sichtbar werden. |

## Einblendungen: freier Text, eine Schrift
Alle Text-Bausteine haben `box=False` (True = schlichte dunkle Fläche, nur im Notfall), `blur=None` (automatisch: an im
Bildschirm-/Split-Teil, aus im Talking Head) und meist `align='left'|'center'|'right'`. Die Parameter `icon` und `light`
werden aus Kompatibilität angenommen, aber ignoriert. Labels (`kicker`) nur setzen, wenn sie Information tragen, sonst `''`.

| Methode | Wofür | Hinweise |
|---|---|---|
| `tile(id,t0,t1,pos,kicker,title,sub=None,w=600,size=54)` | Tipp, Begriff, Fakt, Namens-Bauchbinde | Headline Wort für Wort, Unterzeile Regular |
| `listcard(id,t0,t1,pos,kicker,title,items,w=640,isize=40,num=False)` | Aufzählungen, Prompt-Inhalte, Recap, Roadmap | `items=[(S(t),'Text'),…]`: Punkte **untereinander als Text**, jeder erscheint beim Aussprechen; `num=True` setzt dezente „01“ davor |
| `chips(id,t0,t1,pos,kicker,items,w=600,row=False,size=40)` | Tools, Tech-Stack, Nischen | untereinander; `row=True` = eine Zeile mit „·“ |
| `search(id,t0,t1,pos,kicker,queries,w=700)` | getippte Suchen | schlichte dunkle Suchleiste (echtes UI-Objekt) |
| `learning(id,t0,t1,n,text)` | Kern-Takeaway („Learning #n“) | Bild abgedunkelt + geblurrt, große Headline frei im Bild, Kamera scharf; im Vollbild-Talking-Head die Person scharf im 9:16-Rahmen links, Text rechts; 2–4 pro Video |
| `chapter(id,t0,t1,n,title,total=4,letterbox=True,label=None)` | Kapitelstart | Titelkarte mit **Kinobalken**, Abdunklung, feiner Fortschrittslinie; Kamera bleibt scharf; Label aus `profil.texte.schritt` |
| `tag(id,t0,t1,pos,text,size=38,pill=False)` | kurzer Hinweis/Status | freie Textzeile; `pill=True` = helle Pille, nur wenn es UI-artig sein soll |
| `quote(id,t0,t1,pos,kicker,text,w=900,size=60)` | Schlüsselsatz wörtlich | Headline in Anführungszeichen (`profil.texte.zitat_auf/zu`), Akzentwort möglich |
| `compare(id,t0,t1,pos,kicker,title,bars,w=700)` | Vorher/Nachher-Zahlen, Aufwand | `bars=[(S(t),'Label',0–100,'var(--marke3)','Wertlabel'),…]`, feine 6-px-Balken |
| `textbehind(id,t0,t1,kicker,word,y=150,size=280,sub=None,speed=200)` | großes Wort **hinter** der Person, läuft **langsam** als Laufband einmal von rechts nach links durch | nur Vollbild-Talking-Head / Kamera-Einschub. **`t1=None`** = Fenster automatisch passend zu `speed` (≈ 8–12 s); für `wide_at` vorher `tb = tb_window(S(t0), 'Wort')` rechnen und `c.textbehind(…, tb[0], None, …)`. `kicker` wird nicht angezeigt (`show_kicker=True` holt ihn zurück). Warnung über 240 px/s. `ticker=False` = stehendes Wort |
| `community(id,t0,t1,bullets,pill_at,browser_pos=None,text_pos=None,bw=960,tw=640,nodim=False)` | große CTA-Einblendung (Texte aus `profil.cta`, Screenshot `assets/cta.jpg`) | Screenshot im schlichten Browserrahmen, Vorteile als Textzeilen, Akzent-Pille. Im Split-Layout z. B. `text_pos={"left":660,"top":110}, tw=560, browser_pos={"left":1250,"top":230}, bw=620`. `nodim=True`, wenn die Person sichtbar bleiben soll |
| `outro_cta(id,t0,pos=None)` | CTA im Outro | Screenshot + Headline + Pille, bleibt bis Segmentende |
| `subscribe(id,t0,pos=None)` | Abo-Störer mit Kanalname, Handle und Kanalbild aus `profil.kanal` (ohne Bild: Initialen): Mauszeiger klickt „Abonnieren“ → „Abonniert ✓“, Glocke klingelt | ~6,2 s; Position aus `project.json → subscribe_pos`. Bleibt eine Pille (echtes UI-Objekt) |
| `before_after(id,switches)` | „Vorher“/„Nachher“-Label | schlichte Textzeile oben mittig, `switches=[(S(t),0|1),…]` |
| `sponsor(id,t0,t1,type_at=None,headline=None,mode=None)` | bezahlte Kooperation: große weiße Partner-Einblendung, Logo, Rabattcode wird getippt, „Code angewendet“ | braucht `"sponsor"` in project.json; `panel` über dem Bildschirm (Split) oder `full` mit der Person im 9:16-Rahmen (Vollbild). Alles Weitere in `werbepartner.md` |
| `sponsor_link(id,t0,t1,type_at=None)` | Partner-Link als weiße Pille mit Icon, Link wird getippt | „ich blende dir den Link ein“ |
| `raw(html, js_lines, sfx)` | alles andere | IDs eindeutig, nur Transform/Opacity/Filter animieren. Für Text die Klassen `.hl .li .tx .lbl .sh` und `words()`/`rich()` nutzen, für Lesbarkeit `<i class="sc"></i>` (+ `<i class="sb"></i>`) vor `<div class="ct">…</div>` und `c._reveal(id,t0,t1)`, siehe `_block` in lib.py |

Eigene Diagramme mit `raw()` als freie SVG-Linien im Bild, nicht als Kachel.
Sound-Effekte kommen nur bei Kapiteln (whoosh), Learnings und Text-hinter-Person (whoosh-cinematic, leise),
CTA, getippten Suchen, Partner-Einblendungen und dem Abo-Störer automatisch mit. Normale Texteinblendungen sind still.

**Ältere Storyboards** (vor Version 2 des Skills) laufen weiter: alte Parameter wie `icon=`, `light=`, `icons=` werden
angenommen und ignoriert, `textbehind` mit festem Fenster warnt nur, wenn es zu schnell wird.

## Gast-Format (Porträt/Interview) – Details in `intro-steckbrief.md`
| Methode | Wirkung |
|---|---|
| `c.intro(cid, t0, gast=None, rolle=None, folge=None, titel=None, dur=6.4)` | Marken-Intro über dem laufenden Video: Abdunkeln + Blur, schräger Akzent-Strich, Logo + Kanalname, Zeile „Folge n / Gast, Rolle“, Abgang als schräger Doppel-Wisch. Werte aus `project.json → gast`, wenn nicht übergeben. Jingle als Musikfenster `track: "jingle"`. |
| `c.steckbrief(cid, t0, t1, name=None, rolle=None, fakten=None, w=620)` | Gast-Steckbrief frei im Bild gegenüber dem Gesicht: Label mit Akzentstrich, Name groß, Rolle, 3–5 Zeilen „Label · Wert“. `fakten=[(Label, Wert)]` oder `[(t, Label, Wert)]`. |
| `c.ortsmarke(cid, t0, t1, label=None, detail=None, stadt=None, pos=None)` | Pin mit Pulsring, Stadt klein, Ortsteil groß, Detailzeile; Standard unten links. |
