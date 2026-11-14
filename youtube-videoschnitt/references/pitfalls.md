# Fallstricke aus echten Produktionen

**Schnitt**
- Whisper-Wortzeiten (large-v3-turbo) liegen bis ±0,3 s daneben und setzen Wörter gern in Stille. Schnitte daher
  nur über den Pegel (edl.py), Wortzeiten nur für Einblendungs-Trigger.
- Die ersten Wortzeiten liegen oft 1–2 s zu früh (Video beginnt in Stille). Hook-Einblendungen am Pegel ausrichten.
- `manual_remove` nie nach Wortzeiten setzen: In einer früheren Produktion endete ein Wort laut Whisper 0,16 s vor
  dem echten Wortende, der Schnitt kappte es („mitten im Satz“). Vorher den Pegel in 0,1-s-Schritten ansehen und
  erst in der Stille beginnen.
- Leise Wortanfänge abgeschnitten? In project.json `thr_db` (Pausenschwelle) und `loud_db` (Warnschwelle für
  weggeschnittenen lauten Ton) fest setzen. Ohne Angabe hängen beide vom Sprachpegel des ganzen Videos ab.
- Pausen genau auf der Schwelle können durch Gleitkomma-Rundung mal behalten, mal gekürzt werden. edl.py hat dafür
  eine Toleranz von 1e-6 s. Ein `manual_remove` kann nach einer Zeitverschiebung trotzdem um 1 Frame anders
  einrasten → das betroffene Segment neu rendern.
- `force_keep` schützt Bereiche vor jedem Kürzen: stille Lücken für eingeschobene Sequenzen, Zeitraffer, Stellen,
  an denen ein Video im Bild läuft, dessen Ton nicht aufgenommen wurde.
- Lange stille Handarbeit (z. B. 2 min Werkzeug umstecken) als Zeitraffer direkt in die Arbeitsdatei bauen (jedes
  8. Bild, stumm) und per `force_keep` schützen. Musik dort auf Sprachniveau, Whoosh rein und raus.
- Eine einzige `select`-Filterzeile mit 300+ Bereichen bricht ffmpeg ab („Cannot allocate memory“) → render_base.py
  rendert in Blöcken à 30 Bereichen.
- render_base.py verwendet vorhandene `chunks/c_XX.mp4` wieder. Nach einer Änderung an edl/timemap die betroffenen
  Blöcke löschen (Block = 30 Abschnitte, Index aus edl.json), sonst meldet es „ABWEICHUNG“ bei der Frame-Zahl.
- `camera_cuts` nicht ändern, während render_base.py läuft: Die Blöcke hängen an der Schnittliste.
- ffmpeg 8: `-filter_script` heißt jetzt `-/filter:v datei`; `-vsync` heißt `-fps_mode`.
- In Demo-Passagen (Website scrollen) keine Pausen kürzen, sonst fehlt genau das, was man sehen soll.
- **Inhalte nicht kürzen**, wenn `schnitt.inhalt_kuerzen` false ist: Raus dürfen nur Pausen, Versprecher, echte
  Wiederholungen und reines Formular- oder Dropdown-Ausfüllen. Länge ist nur eine Richtlinie, nie mitten im Satz
  schneiden, um eine Ziellänge zu treffen.
- Neuansätze konsequent raus, auch wenn beide Fassungen „irgendwie passen“: Gewünscht ist meist nur der zweite.
- Segmentgrenzen nur an Schnittpunkte (timemap-Zeilen) legen, sonst springt der Push-in-Zoom mitten im Satz.

**Transkription**
- **Whisper-Schleife:** In einer früheren Produktion wiederholte Whisper ab ~12 min nur noch denselben Satz bis zum
  Ende. `transcript/lines.txt` immer bis zum Schluss überfliegen. Lösung: Rest in 60–95-s-Stücken neu transkribieren
  und mit Versatz einfügen.
- Kurze Stellen, die nach Versprecher aussehen, mit einem eigenen Whisper-Lauf auf 6–10 s Ton gegenprüfen. Mehrere
  vermeintliche Versprecher waren nur Transkriptionsfehler.
- Transkriptions-Modell: hyperframes lädt sonst 3 GB large-v3; check_env.sh verlinkt ein vorhandenes turbo-Modell.

**Mehrere Aufnahmen, Lippensynchronität**
- Szenen per concat-Demuxer (`-c copy`) verkettet → die Edit-Liste der AAC-Spur (~44 ms Encoder-Vorlauf) geht
  verloren, der Ton rutscht pro Szene weiter nach hinten (bis ~100 ms). Ton immer je Datei aus dem Original
  dekodieren, auf die Bildlänge (Frames/30) kürzen oder auffüllen und dann zusammensetzen. Prüfen:
  Kreuzkorrelation Original ↔ source_audio.wav = 0 ms.
- Ausschnitte frame-genau seeken: immer `(f0 - 0.5)/30` plus `-frames:v`, nie `-ss t0:.4f` (je nach Rundung
  1 Frame zu spät). build.py und render_base.py machen das so, eigene Stück-Renderer ebenfalls.
- Lippensync Frame für Frame gegen die Original-Datei messen, nicht über Bewegungsverläufe.
- Direktes MP4-concat mit gemischten Encodern bricht ab („Invalid NAL unit size“). Bei knappem Speicher ohne
  Neukodierung: jedes Stück per `h264_mp4toannexb` (HEVC: `hevc_mp4toannexb`) nach MPEG-TS, die TS-Dateien per
  concat-Demuxer in MP4 kopieren, nur Lücken oder Zeitraffer neu kodieren. Prüfen: Frame-Differenz an jedem
  Übergang gegen das Original = 0.

**Kamera-Synchronisation**
- Kameraspuren haben oft eine stumme Tonspur (−91 dB) → Ton-Kreuzkorrelation unmöglich, Bild nutzen.
- Messfenster am Videoanfang: Der Suchbereich vor Sekunde 0 muss mit Nullen aufgefüllt werden, sonst verrutscht der
  Versatz um genau diese Sekunden. Ist in sync_cam.py behoben.
- In Split-Abschnitten schaut die Person ruhig auf den Bildschirm → schwache Korrelation. Vollbild-Abschnitte nehmen.
- **Versatz springt:** OBS verliert gelegentlich Frames. In einer früheren Produktion lag der Versatz bis ~560 s bei
  −1, um 600 s bei +1 und ab 680 s bei 0 Frames. Vor render_base.py an jedem Kamera-Einschub messen (sync_cam.py mit
  `--win` als 30-s-Fenster und `--region` des Kamerabereichs) und abweichende Werte in `camera_cut_offsets`
  eintragen (gleiche Reihenfolge wie `camera_cuts`, Sekunden). Kontrolle: Standbilder 1 Frame vor und nach jedem
  Einschub-Ende.
- Layout-Grenzen bei OBS-Szenenwechseln ohne Blende: erst 2-fps-Mini-Bilder für die Übersicht, danach 30 fps um jede
  Grenze. Ein Kapitel exakt an der Grenze landet sonst im falschen Segment.

**HyperFrames**
- `letterSpacing`, `width`, `height` nicht animieren → Lint-Fehler `gsap_non_transform_motion`. Buchstaben einzeln
  mit `y`/`opacity` animieren, Balken per `scaleX`.
- Kein `transform` im Inline-CSS, wenn später ein `tl.to` dieselbe Eigenschaft animiert → Lint-Fehler
  `gsap_css_transform_conflict`. Start per `fromTo` setzen.
- In `fromTo` mit `opacity:0` die Deckkraft auch im Ziel setzen (`opacity:1`), sonst Lint-Fehler
  `gsap_cold_seek_hidden_fromto_missing_reveal` und unsichtbare Elemente in kalten Render-Workern.
- **Element-IDs müssen mit einem Buchstaben anfangen** und dürfen nur Buchstaben, Ziffern, `-` und `_` enthalten.
  IDs wie `'143'` oder `'plan$'` machen den CSS-Selektor in GSAP ungültig, die Zeitleiste bricht ab und das GANZE
  Segment bleibt ohne Einblendungen. Lint meldet das nicht, nur die QA-Bilder zeigen es (leeres Bild am Cue).
- Viele Bild-Elemente mit `filter` (z. B. 26 fallende Objekte mit blur/drop-shadow) lösen die Lint-Warnung
  `composition_heavy_overlay_count_high` aus → Gefahr schwarzer Frames. Tiefe nur über Größe und Opacity, kein
  `filter` auf Partikeln. Lint nach jedem Build auf diese Warnung prüfen.
- Schriftfamilien brauchen `@font-face` im Dokument (lib.py bettet die Profil-Schriften ein), sonst Fallback-Schrift.
  Stimmt der Familienname in `profil.marke.schriften` nicht mit dem in `fonts.css` überein, erscheint ebenfalls die
  Fallback-Schrift → `vorschau.py` zeigt es sofort.
- `backdrop-filter` funktioniert nur, wenn das Video im selben Render liegt. Deshalb wird jedes Segment MIT dem
  Videoausschnitt gerendert, nicht als transparentes Overlay.
- Opacity eines Elterns blendet auch seinen Blur. `_reveal` blendet deshalb Schatten und Blur (`.sc`, `.sb`, `.pn`)
  und Text (`.ct`) einzeln ein und setzt den Container nur hart auf sichtbar. Eigene `raw()`-Bausteine genauso bauen.
- Quellen mit langer GOP frieren beim Seek ein → Ausschnitte immer mit `-g 15` neu kodieren (build.py).
- **`bg.mp4` passt nicht mehr:** Verschiebt eine nachträgliche Einblendung oder ein geänderter Schnitt eine
  Segmentgrenze, zeigte das Segment früher den alten Ausschnitt (Mund nicht synchron, am Ende Standbild). build.py
  schreibt deshalb `segs/<id>/bg.key` (Startbild, Bildzahl, Stand von base.mp4) und baut `bg.mp4` samt
  Freistellungen neu, wenn er nicht passt. Trotzdem nach jeder Änderung prüfen: Kamerabereich im Render gegen
  base.mp4 vergleichen (mittlere Abweichung ≈ 2–5 passt, ≈ 15 ist versetzt).
- Freistellung (`remove-background`, u2net) läuft mit ~2,3 fps in 4K. Nur die Text-hinter-Person-Fenster
  freistellen, nicht ganze Abschnitte. Qualität `best`.
- Freistellung von Bildern auf grauem Studiogrund: u2net frisst Teile langer oder silbriger Objekte weg. Besser:
  Randfarbe als Hintergrund nehmen, Flood-Fill von außen (Farbabstand < 14), Kante weich, Farbe am Rand entmischen.
- HyperFrames legt Snapshots je nach Version unter `segs/<id>/snapshots/` oder
  `segs/<id>/.hyperframes/artifacts/snapshots/<uuid>/` ab. qa.py und vorschau.py suchen beide Orte.

**Rendern**
- **Render-Sperre:** HyperFrames lässt pro Benutzerkonto nur ein `hyperframes render` gleichzeitig laufen, weitere
  warten still („Waiting for another render to finish“ im Log). Paralleles Rendern lief so faktisch nacheinander.
  render_all.sh setzt `HYPERFRAMES_RENDER_LOCK=off` und rendert mit 3 Spuren × 4 Worker (gemessen auf einem M4 Max:
  168 s mit Sperre, 135 s mit 3 Spuren; 4 Spuren bringen nichts mehr, nur mehr Last). Eigene Render-Aufrufe
  außerhalb von render_all.sh ohne die Variable warten weiter auf laufende Renders.
- ffmpeg nimmt beim Rendern immer alle Kerne (nicht abschaltbar), deshalb laufen die Renders mit `nice 10`. Wer
  nebenher arbeiten will oder wenig RAM hat: `RENDER_LANES=1 RENDER_WORKERS=4 bash render_all.sh`.
- 4K-Rendering: ~2× Echtzeit der Segmentdauer mit 3 Spuren.
- Nie zwei Render-Warteschlangen gleichzeitig: `pkill -f render_all.sh` beendet die `xargs`-Kinder nicht → zwei
  Warteschlangen, Kollisionen beim Verschieben der Temp-Dateien. render_all.sh hat einen Lock; vor einem Neustart
  alle `hyperframes render`-Prozesse per PID beenden und mit `ps aux | grep "hyperframes render"` prüfen.
- **Speicherplatz:** Multi-Worker-Renders schreiben jedes Bild auf die Platte (~16 GB für 2 min 4K) und brechen bei
  wenig Platz mit „Disk capture may need …“ ab. render_all.sh schaltet unter 40 GB frei auf eine Spur mit
  `HF_CAPTURE_PARALLEL_STREAM=true`, unter 100 GB auf zwei. `$TMPDIR/hyperframes-extract-cache-*` kann auf 10 GB
  wachsen und darf gelöscht werden, `chunks/` nach render_base.py ebenso.
- Arbeitsordner nie in einem Cloud-synchronisierten Ordner anlegen (z. B. Schreibtisch oder Dokumente mit iCloud):
  Bei knappem Speicher lagert macOS große Dateien aus („dataless“) → ffmpeg „Operation timed out“, dazu
  Konfliktkopien „… 2.mp4“. Prüfen mit `ls -lO`, zurückholen mit `brctl download <datei>`.
- **Nur betroffene Segmente neu rendern:** Bleibt ein Segment in Startbild, Dauer und `index.html` gleich, ist der
  alte Render gültig (Zeitverschiebung durch geänderte Schnitte davor ist egal, assemble.py legt nach
  `manifest.t0`). Die übrigen: `bg.mp4` und `renders/<id>.mp4` löschen, `build.py <ids>`, render_all.sh.
- Wer ein fertiges Video verlängert und alte Renders wiederverwenden will: `thr_db`/`loud_db` auf die alten Werte
  festsetzen (die Schwelle hängt sonst vom ganzen Ton ab) und `index.html` alt gegen neu vergleichen.
- zsh teilt `$VAR` nicht in Wörter: `for id in $IDS` läuft einmal mit dem ganzen String, nichts wird gelöscht.
  `${=IDS}` oder `bash -c` nehmen. Globs ohne Treffer brechen `rm` in zsh ab, dann einzeln löschen. Danach prüfen,
  ob `bg.mp4` und Renders wirklich weg sind.
- Hardware-Encoder (`h264_videotoolbox`) ignoriert `-b:v` bei ruhigem Material weitgehend, fürs Endprodukt x264
  CRF 16 (assemble.py). ~13 Mbit/s sind bei Bildschirmaufnahmen inhaltsbedingt normal.

**Positionsprüfung**
- Vor jedem Rendern `check_layout.py` laufen lassen (misst im echten Browser-Layout, meldet RAND und GESICHT).
  Einblendungen am Rand oder vor dem Gesicht waren der häufigste Kritikpunkt.
- Mit vielen Segmenten auf einmal kann check_layout.py leer zurückkommen (JSON-Fehler) → je Segment einzeln aufrufen.
- Positionen nach dem überwiegenden Layout im Einblendungsfenster wählen, nicht nach dem ersten Bild. Im
  Schnelldurchlauf wechselt das Layout ständig → Einblendungen dort unten links ohne Blur, Zähler kurz ausblenden.
- Listen im Vollbild wirken schnell zu nah am Gesicht: check_layout.py sperrt deshalb ±390 px um die Gesichtsmitte
  inklusive Push-in-Zoom.

**Musik und Ton**
- MusicGen-Clips sind 30 s; Verlängerung per Fortsetzung (10 s Kontext + 20 s neu). Fortsetzungen enthalten
  gelegentlich 1–3 s Stille oder kippen in leise Passagen, music.py findet und schneidet das heraus.
- Die erste Generierung lädt ~3,5 GB Modell nach `~/.cache/huggingface`.
- **Musikfenster in Quellzeit** eintragen (mix.py wendet `S()` an). Schnittzeiten führen zu „zu kurz → wird geloopt“.
- **Originalton mit Musik** (Spiel, Demo-App): hebt den Grundpegel (Pausen ≈ −45 statt −60 dBFS). Erkennen: Pegel der
  leisesten 8 % je Abschnitt vergleichen. Dort keine eigene Musik, im Bildschirmteil keine Sound-Effekte, in
  Kamera-Passagen darüber halbe Lautstärke, als Filter über `c.sfx` am Ende von story.py. Pausen dort mit
  `demo_ranges` (0,8 s) großzügig stehen lassen, sonst springt die Hintergrundmusik bei jedem Schnitt.
- Beim Vorspulen kein durchgehendes Rauschen: ein Whoosh beim Rein-, einer beim Rausspulen, dazwischen trägt die Musik.
- Applaus oder laute Effekte mit Gain ≤ 0,3, sonst liegen sie über der Stimme (gemessen bei 0,55: −20,6 LUFS gesamt
  gegen −25,3 LUFS Stimme).
- **Doppelte Stimme:** Führt in einer OBS-Szene eine zweite Quelle (z. B. die Kamera) das Mikro ohne Sync-Versatz mit,
  entsteht ein hörbares Echo nur in dieser Szene. Vor dem Schnitt prüfen: Autokorrelation der Tonspur je Abschnitt,
  ein Peak ≥ 0,2 bei 50–500 ms bedeutet doppelte Quelle; Pegel 4–5 dB höher als in anderen Szenen ist ein weiteres
  Indiz. Beheben in OBS (Audio der Zusatzquelle stumm), eine nachträgliche Reparatur ist sehr aufwendig.

**Einblendungen (Clean-Stil)**
- Standard ist freier Text in der Profilschrift mit weichem Schatten, ohne Kacheln und ohne Icons. `icon`- und
  `light`-Parameter alter Storyboards werden ignoriert, Icons also nicht nachbauen.
- Freier Text über hellen Webseiten: Der Schatten hilft, weißer Text auf weißem Dialog bleibt trotzdem schwer. Die
  Position auf eine dunklere oder ruhigere Stelle legen statt die Abdunklung hochzudrehen; bei sehr unruhigem
  Hintergrund `box=True`.
- **Text hinter der Person:** Der Kopf verdeckt ~450 px in der Bildmitte, stehende Wörter sind kaum lesbar
  („Ein Spiel“ → „Eir piel“). Deshalb läuft `textbehind` als Laufband (Standard). Kurz halten; mit `t1=None` rechnet
  `tb_window()` das Fenster für ~200 px/s aus, lib.py warnt bei zu schnellem Laufband. Lange Begriffe lieber als
  Zitat. Breite aus den echten Glyphenbreiten der Profil-Schrift (`breiten.json`, `text_width()`).
- **Taglines bei Text-hinter-Person** hell und außerhalb des Zoom-Wrappers (sonst schlecht lesbar oder abgeschnitten).
- **Push-ins** nicht zu stark (Standard max. 1,11) und Transform-Ursprung über dem Kopf (y ≈ 12 %), sonst sind die
  Haare oben abgeschnitten.
- Satzzeichen ohne Leerzeichen (`*Leben*.“`) hängt `words()` ans Wort und hält sie per `nowrap` zusammen, `.hl` hat
  `text-wrap:balance` gegen einzelne Wörter in der letzten Zeile. In eigenen `raw()`-Bausteinen beides übernehmen.
- **Durchgestrichene Begriffe** (eigene `raw()`-Variante): `white-space:nowrap`, sonst bricht ein langer Begriff um
  und der Strich läuft zwischen den Zeilen.
- **`community()` im Vollbild-Talking-Head:** `nodim=True`, sonst ist die Person die ganze Zeit geblurrt.
- **Zähler** erst auf die zuerst genannte Zahl laufen lassen und bei einer Korrektur weiterzählen. Bei Serien die
  Endzahl nicht vorwegnehmen („Calls 07“ statt „07/25“).
- **Begriffe, die nur wiederholen, was gerade im Bild passiert** (Dropdown-Status, Mausklicks), weglassen.
- **Kapitel und Learnings im Vollbild:** Person scharf im 9:16-Rahmen links, Text daneben, nicht alles blurren.
  Große Übersichten im Vollbild nicht auf Augenhöhe, sondern unten rechts. Standzeit ~4 s.

**Werbekennzeichnung (bezahlte Kooperation)**
- Hat project.json `sponsor`, setzt assemble.py das Wort „Werbung“ (`profil.texte.werbung`) oben rechts ein. Mit
  `ad_label_ranges` nur dort, wo über den Partner gesprochen wird; die Bereiche stehen in QUELLZEIT wie im Storyboard.
  `ad_label: false` schaltet es ab. Zusätzlich beim Hochladen die Plattform-Kennzeichnung setzen und in den Texten
  (Beschreibung usw.) darauf hinweisen.
- Die `sponsor`-Einblendung nie über die echte Code-Eingabe im Checkout legen, sondern direkt danach. Standzeit ≥ 7 s,
  damit der Code lesbar ist.
- Weißer Text über weißen Partnerseiten ist unlesbar: dort die Zeile über dem Bildschirmbereich nehmen.

**Resolve-Export**
- export_resolve.py schreibt Final-Cut-7-XML, kein FCPXML: FCPXML kennt keine festen Tonspuren, Resolve verteilt
  verbundene Clips dann wild auf A1/A2.
- V3 enthält die fertigen Grafik-Blöcke deckend, mit eingebackenen Push-ins. Zum Arbeiten am Schnitt V3
  ausschalten, sonst sieht man V1/V2 nicht.
- Erst nach render_base.py, render_all.sh und mix.py aufrufen. Die Kamera-Einschübe nutzen denselben Ausschnitt und
  dieselben `camera_cut_offsets` wie render_base.py; stimmt dort etwas nicht, ist auch V2 versetzt.

**Assets**
- Codex-CLI-Pfad ändert sich mit App-Updates: `find /Applications/ChatGPT.app -name codex -type f`.
- Cookie-Banner auf Screenshots: nur „Nur notwendige“ klicken.

**Fremde Stimmen und private Daten**
- Gesprächspartner über Lautsprecher dürfen oft nicht ins Video. Erkennen: Telefonstimme hat kaum Bass
  (80–250 Hz ≈ 20–38 dB unter 300–3400 Hz) und ist ~10 dB leiser. Solche Abschnitte stumm schneiden oder als
  stummen Fast-Forward (`lib.S()` kann Geschwindigkeit als 5. Feld der Zeitkarte).
- Kommentar-Blöcke nach einem Telefonat nie vor ihrem Startpunkt beginnen lassen (kein Vorlauf). Die geschnittene
  Tonspur danach komplett neu transkribieren und nach Grußformeln („Tschüss“, „Danke“, „Hallo“) an
  Abschnittsgrenzen suchen: Dort rutschen am häufigsten Reste der fremden Stimme durch.
- Personennamen Dritter auf Wunsch piepen. Piepen vor edl.py in `source_audio.wav`/`audio16k.wav` einsetzen, dann
  landet es automatisch in Schnitt und Mix; im exportierten Transkript die Stellen durch `[piep]` ersetzen.
- Bildschirminhalte mit personenbezogenen Daten (E-Mails, Telefonnummern, Kundennamen) blurren. Auch wenn die Person
  sagt, es sei schon geblurrt: selbst prüfen. Benachrichtigungen (Kalender-Popups) und Seitenleisten mit Chat- oder
  Projekttiteln tauchen oft unbemerkt auf. Bei Zoom-Übergängen, Schnitten und schnellem Scrollen bleiben sonst
  Einzelbilder lesbar, deshalb jedes Bild prüfen und zum Schluss das fertige Video noch einmal kontrollieren.
