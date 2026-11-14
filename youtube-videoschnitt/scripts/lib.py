"""Bausteine für die Einblendungen (HyperFrames-Kompositionen) im Designsystem aus dem Kanal-Profil.

Wird vom Storyboard (Arbeitsordner/story.py) importiert. Liest project.json und timemap.json im Arbeitsordner
und das Profil (profil.py: Farben, Schrift, Texte, Kanal, CTA).
Koordinaten sind immer CSS-Pixel im 1920×1080-Raster (gerendert wird mit DPR 2 → 4K).

Stil (references/design-system.md): eine Schrift, Text frei im Bild mit weichem Schatten, kaum Flächen,
ruhige filmische Bewegung. Flächen nur für echte Objekte (Screenshot, Suchleiste, Abo-Button, CTA-Pille).
"""
import json, os, re, html as H
import profil as PR

SKILL = PR.SKILL
WORK = os.environ.get('YT_WORK') or os.getcwd()
CFG = json.load(open(os.path.join(WORK, 'project.json')))
FPS = CFG.get('fps', 30)
FONTS = PR.fonts_css()
T = PR.get('texte')                       # sprachabhängige Beschriftungen
F = PR.get('marke.farben')                # Farb-Tokens
RGB = {k: PR.hex_rgb(v) for k, v in F.items()}
SANS = PR.get('marke.schriften.text') or 'Poppins'
CTA = PR.get('cta') or {}
_tm = os.path.join(WORK, 'timemap.json')
TM = json.load(open(_tm)) if os.path.exists(_tm) else []
# Einträge: [quelle_von, quelle_bis, schnitt_start, typ] oder mit 5. Feld Geschwindigkeit (Fast-Forward, z. B. 24).
# Typ 'X' = Einschub außerhalb der Reihenfolge (Cold Open, Supercut) – zählt nicht für S().
_sp = lambda r: r[4] if len(r) > 4 else 1
OUT_DUR = max((r[2] + (r[1] - r[0]) / _sp(r) for r in TM), default=0.0)
LAYOUT = CFG.get('layout', {})


def S(t):
    """Quellzeit (Originalvideo) → Zeit im geschnittenen Video."""
    main = [r for r in TM if r[3] != 'X']
    for r in main:
        if r[0] <= t < r[1]:
            return r[2] + (t - r[0]) / _sp(r)
    nxt = [r[2] for r in main if r[0] > t]
    return min(nxt) if nxt else OUT_DUR


def q(t):
    return round(round(t * FPS) / FPS, 4)


def rich(s):
    """*wort* → Akzent. Nur eine Schrift: In Headlines ist das Akzentwort voll hell, der Rest leicht
    zurückgenommen; in Fließtext wird es Semibold."""
    s = H.escape(s)
    return re.sub(r"\*(.+?)\*", r'<span class="acc">\1</span>', s)


def words(s):
    """Wie rich(), aber jedes Wort als eigene Spanne – für die Wort-für-Wort-Einblendung von Headlines.
    Satzzeichen und Anführungszeichen ohne Leerzeichen bleiben am Wort (kein „Leben ." oder Umbruch davor)."""
    groups, prev_space = [], True
    for part in re.split(r'(\*[^*]+\*)', s):
        if not part:
            continue
        acc = part.startswith('*') and part.endswith('*') and len(part) > 2
        txt = part[1:-1] if acc else part
        glue = bool(groups) and not prev_space and not txt[:1].isspace()
        for k, w in enumerate(txt.split()):
            span = f'<span class="w{" acc" if acc else ""}">{H.escape(w)}</span>'
            if k == 0 and glue:
                groups[-1].append(span)
            else:
                groups.append([span])
        prev_space = txt[-1:].isspace()
    return ' '.join(g[0] if len(g) == 1 else '<span style="white-space:nowrap">' + ''.join(g) + '</span>' for g in groups)


def _cam_mask_css():
    """Maske, die nur die Facecam aus dem Video freilegt (für 'Kamera scharf über Blur')."""
    cam = LAYOUT.get('cam')
    if not cam:
        return 'display:none'
    if cam['shape'] == 'circle':
        cx, cy, r = cam['cx'], cam['cy'], cam['r']
        g = cam.get('glow', 40)  # weicher Auslauf für den Glow-Ring
        m = f"radial-gradient(circle at {cx}px {cy}px,#000 0,#000 {r+3}px,rgba(0,0,0,.55) {r+16}px,transparent {r+g}px)"
        return f"-webkit-mask-image:{m};mask-image:{m}"
    x, y, w, h, rad = cam['x'], cam['y'], cam['w'], cam['h'], cam.get('radius', 0)
    return f"clip-path:inset({y}px {1920-x-w}px {1080-y-h}px {x}px round {rad}px)"


def _css():
    c = r"""
:root{--tinte:@tinte;--papier:@papier;--basis:@basis;--basis2:@basis2;--marke1:@marke1;--marke2:@marke2;--marke3:@marke3;--akzent:@akzent;--grau:@grau;--sand:@sand;--ink:var(--tinte);--cream:var(--papier);--jungle:var(--basis);--jungle2:var(--basis2);--tealdeep:var(--marke1);--teal:var(--marke2);--aqua:var(--marke3);--lime:var(--akzent);--muted:var(--grau)}
*{box-sizing:border-box}
html,body{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#000;font-family:'@SANS',ui-sans-serif,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
#root{position:relative;width:100%;height:100%;overflow:hidden}
.vw{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:50% 50%}
.vw video,.cam video,.zr video{position:absolute;left:0;top:0;width:1920px;height:1080px;object-fit:cover;display:block}
.cam{position:absolute;left:0;top:0;width:1920px;height:1080px;__CAMMASK__}
.zr{position:absolute;overflow:hidden;opacity:0}
.zr .zi{position:absolute;left:0;top:0;width:1920px;height:1080px}
.serif{font-family:inherit;font-style:normal;font-weight:inherit;letter-spacing:inherit}
.card{position:absolute;opacity:0;color:var(--papier);isolation:isolate}
.hl{font-weight:600;letter-spacing:-.04em;line-height:1.08;text-wrap:balance}
.hl:has(.acc){color:rgba(@R_papier,.62)}
.hl .acc{color:var(--papier)}
.hl .w{display:inline-block}
.tx{font-weight:400;letter-spacing:-.01em;line-height:1.4;color:rgba(@R_papier,.86)}
.tx .acc,.li .acc{font-weight:600;color:var(--papier)}
.li{font-weight:600;letter-spacing:-.025em;line-height:1.22}
.lbl{font-size:25px;font-weight:600;letter-spacing:-.01em;color:rgba(@R_papier,.7);margin-bottom:12px}
.sh{text-shadow:0 1px 2px rgba(0,0,0,.28),0 3px 26px rgba(0,0,0,.5)}
.ct{position:relative}
.sc,.sb,.pn{position:absolute;opacity:0;pointer-events:none}
.sc{inset:-96px -130px;border-radius:200px;background:radial-gradient(closest-side,rgba(@R_basis,var(--sa,.3)),rgba(@R_basis,calc(var(--sa,.3)*.75)) 55%,rgba(@R_basis,0));filter:blur(60px)}
.sb{inset:-70px -100px;-webkit-backdrop-filter:blur(20px) brightness(.9);backdrop-filter:blur(20px) brightness(.9);
-webkit-mask-image:linear-gradient(to right,transparent,#000 130px,#000 calc(100% - 130px),transparent),linear-gradient(to bottom,transparent,#000 90px,#000 calc(100% - 90px),transparent);-webkit-mask-composite:source-in;
mask-image:linear-gradient(to right,transparent,#000 130px,#000 calc(100% - 130px),transparent),linear-gradient(to bottom,transparent,#000 90px,#000 calc(100% - 90px),transparent);mask-composite:intersect}
.pn{inset:-28px -34px;border-radius:24px;background:rgba(@R_basis,.76);-webkit-backdrop-filter:blur(30px) saturate(120%);backdrop-filter:blur(30px) saturate(120%);border:1px solid rgba(255,255,255,.07)}
.glass{background:linear-gradient(160deg,rgba(@R_basis2,.72),rgba(@R_basis,.86));-webkit-backdrop-filter:blur(44px) saturate(140%);backdrop-filter:blur(44px) saturate(140%);border:1px solid rgba(255,255,255,.16);border-radius:30px;box-shadow:inset 0 1px 0 rgba(255,255,255,.22),0 30px 90px rgba(0,0,0,.38)}
.glass.light{background:linear-gradient(160deg,rgba(255,255,255,.9),rgba(@R_papier,.82));color:var(--tinte);border-color:rgba(255,255,255,.7);box-shadow:inset 0 1px 0 #fff,0 30px 90px rgba(0,0,0,.30)}
.kicker{display:flex;align-items:center;gap:12px;font-size:20px;font-weight:600;letter-spacing:-.01em;opacity:.72}
.ttl{font-weight:600;letter-spacing:-.04em;line-height:1.08}
.ttl:has(.acc){color:rgba(@R_papier,.62)}
.ttl .acc{color:var(--papier)}
.light .ttl:has(.acc){color:rgba(@R_tinte,.55)}
.light .ttl .acc{color:var(--tinte)}
.sub{font-weight:400;opacity:.8;line-height:1.4;letter-spacing:-.01em}
.sub .acc,.it .acc,.chip .acc{font-weight:600}
.it{opacity:.26}
.chip.it{opacity:0}
.pill{display:inline-flex;align-items:center;gap:16px;padding:12px 12px 12px 28px;border-radius:100px;background:var(--akzent);color:var(--tinte);font-weight:600;font-size:24px;letter-spacing:-.02em}
.pill .arr{width:46px;height:46px;border-radius:50%;background:var(--tinte);color:#fff;display:flex;align-items:center;justify-content:center}
.chip{display:inline-flex;align-items:center;gap:12px;padding:14px 26px;border-radius:100px;font-size:26px;font-weight:600;letter-spacing:-.02em}
.row{display:flex;align-items:center;gap:22px}
.num{flex:none;width:54px;height:54px;border-radius:50%;border:1px solid rgba(255,255,255,.28);display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:600}
.light .num{border-color:rgba(@R_tinte,.2)}
.ico{flex:none;object-fit:contain}
.dim{position:absolute;inset:0;opacity:0;background:rgba(@R_basis,.38);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px)}
.zone{padding:34px 40px;border-radius:34px;background:rgba(@R_basis,.42);-webkit-backdrop-filter:blur(26px) saturate(120%);backdrop-filter:blur(26px) saturate(120%);
-webkit-mask-image:linear-gradient(to right,transparent,#000 30px,#000 calc(100% - 30px),transparent),linear-gradient(to bottom,transparent,#000 26px,#000 calc(100% - 26px),transparent);-webkit-mask-composite:source-in;
mask-image:linear-gradient(to right,transparent,#000 30px,#000 calc(100% - 30px),transparent),linear-gradient(to bottom,transparent,#000 26px,#000 calc(100% - 26px),transparent);mask-composite:intersect}
.zone .glass{-webkit-backdrop-filter:none;backdrop-filter:none;background:rgba(@R_basis2,.75)}
.tb{position:absolute;left:0;width:1920px;text-align:center;color:var(--papier);font-weight:600;letter-spacing:-.04em;line-height:.9;white-space:nowrap}
.sb-btn{position:relative;height:64px;border-radius:100px;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:600;letter-spacing:-.01em;overflow:hidden}
"""
    for k in sorted(F, key=len, reverse=True):
        c = c.replace('@R_' + k, RGB[k])
    for k in sorted(F, key=len, reverse=True):
        c = c.replace('@' + k, F[k])
    return c.replace('@SANS', SANS).replace('__CAMMASK__', _cam_mask_css())


CSS = _css()

ARROW = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7M8 7h9v9"/></svg>'
ARROW_DOWN = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M6 13l6 6 6-6"/></svg>'
CHECK = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'
PIN = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>'
SEARCH = '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>'
STAR = '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/></svg>'
MIC = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>'
CLOCK = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'
BELL = '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>'
CURSOR = '<svg width="54" height="54" viewBox="0 0 24 24"><path d="M5 3l14 7.5-6.2 1.6L10 18.5z" fill="#fff" stroke="__TINTE__" stroke-width="1.4" stroke-linejoin="round"/></svg>'


CURSOR = CURSOR.replace('__TINTE__', F['tinte'])
_W600 = PR.glyph_widths()   # Glyphenbreiten der Textschrift (fett) aus dem Profil


def text_width(word, size, tracking=-0.04):
    """Breite eines .tb-Worts (Textschrift 600, Laufweite −0,04 em) in px – aus den echten Glyphenbreiten."""
    return sum(_W600.get(ch, 0.6) + tracking for ch in word) * size


# Eckenradius des Kamerarahmens relativ zur Rahmenbreite (Learning/Partner im Vollbild). Am besten so wie die eigene
# Kamera-Maske in der Aufnahmesoftware; 0 = eckig. Profil: aufnahme.rahmen_radius (Standard 0,065).
OBS_RADIUS = float(PR.get('aufnahme.rahmen_radius', 0.065))
TB_GAP = 240   # Abstand Laufband ↔ Gesichtsmitte (px) am Start und am Ende


def tb_window(t0, word, size=280, speed=200):
    """(t0, t1) für ein Laufband mit Zielgeschwindigkeit speed px/s – für textbehind(t1=None) und wide_at."""
    return t0, t0 + (2 * TB_GAP + text_width(word, size)) / speed


def free_x():
    """Horizontal freier Bereich (x0, x1) neben einer Rechteck-Kamera; sonst ganze Breite."""
    cam = LAYOUT.get('cam')
    if cam and cam.get('shape') == 'rect':
        if cam['x'] + cam['w'] / 2 < 960:
            return cam['x'] + cam['w'] + 40, 1870
        return 50, cam['x'] - 40
    return 0, 1920


def _load_sponsor():
    """Werbepartner aus project.json → sponsor: "<name>" oder {"partner": "<name>", "code": …}.
    Grunddaten (Logo, Farbe, Code, Link) liegen im Profilordner unter partner/<name>/partner.json
    (references/werbepartner.md), project.json überschreibt einzelne Felder."""
    sp = CFG.get('sponsor')
    if not sp:
        return None
    if isinstance(sp, str):
        sp = {'partner': sp}
    d = PR.partner_dir(sp['partner'])
    assert d, f"Partner „{sp['partner']}“ fehlt: Ordner {PR.PDIR}/partner/{sp['partner']}/ mit partner.json anlegen"
    base = json.load(open(os.path.join(d, 'partner.json')))
    base.update(sp)
    base['dir'] = d
    return base


SPONSOR = _load_sponsor()


def pos_css(p):
    return ';'.join(f'{k}:{v}px' for k, v in p.items())


class Comp:
    """Ein Segment: Video-Ausschnitt (geschnitten) + Karten + Kamera-Bewegung.

    kind: 'th' (Talking Head Vollbild), 'sc' (Screen/Split), 'end' (angehängte Endkarte)
    """

    def __init__(self, cid, out_start, out_end, kind):
        self.id, self.t0, self.t1, self.kind = cid, q(out_start), q(out_end), kind
        self.dur = q(self.t1 - self.t0)
        self.inner_vw = []   # im Video-Wrapper (zoomt bei Push-ins mit)
        self.layers = []     # Overlays über dem Video
        self.js = []
        self.sfx = []        # (Ausgabezeit, Name, Gain)
        self.cutouts = []    # (id, lokal start, lokal ende) – Freistellungen für Text-hinter-Person
        self.cam = False     # Kamera als scharfe Ebene über das Bild legen
        self.nzoom = 0
        self.zooms = []     # Zoom-Ebenen (liegen unter Kamera und Karten)
        self.cues = []      # Einstiegszeiten aller Einblendungen (Ausgabezeit) – qa.py macht dort Kontrollbilder

    def L(self, t_out):
        return q(max(0, t_out - self.t0))

    # ───────── Kamera ─────────
    def th_pushins(self, face=None, wide_at=()):
        """Jump-Cut-Look im Vollbild-Talking-Head: an jedem Schnitt eine andere Einstellung + langsamer Push."""
        face = face or LAYOUT.get('face', [0.5, 0.4])
        self.face = face   # textbehind-Laufband richtet sich danach
        cuts = [r[2] - self.t0 for r in TM if self.t0 - 0.01 <= r[2] < self.t1 - 0.2]
        cuts = sorted(set([0.0] + [q(x) for x in cuts if x > 0.3]))
        self.js.append(f"gsap.set('#vw',{{transformOrigin:'{face[0]*100:.1f}% 12%'}});")   # Ursprung über dem Kopf: Haare bleiben im Bild
        m = (PR.get('schnitt.pushin_max', 1.11) - 1) / 0.11   # stärkster Zoom aus dem Profil (Standard 1,11)
        looks = [(1 + (x - 1) * m, 1 + (y - 1) * m) for x, y in [(1.0, 1.02), (1.06, 1.08), (1.03, 1.05), (1.09, 1.11)]]
        k = 0
        for i, c in enumerate(cuts):
            end = cuts[i + 1] if i + 1 < len(cuts) else self.dur
            if end - c < 0.25:
                continue
            a, b = looks[k % len(looks)]
            if any(w0 - 0.2 <= c + self.t0 <= w1 or c + self.t0 <= w0 <= end + self.t0 for w0, w1 in wide_at):
                a, b = 1.0, 1.03   # Text-hinter-Person braucht die weite Einstellung
            k += 1
            self.js.append(f"tl.set('#vw',{{scale:{a}}},{q(c)});tl.to('#vw',{{scale:{b},duration:{q(end-c)},ease:'none'}},{q(c)});")

    def zoom(self, t0, t1, cx, cy, scale, ease_in=0.8, region=None):
        """Zoom auf einen Punkt (cx, cy in 0..1 der GANZEN Bildfläche) – nur innerhalb des Bildschirmbereichs.

        region: {'x','y','w','h'} in CSS-px; Standard = layout.screen. Die Kamera bleibt dadurch unberührt.
        """
        r = region or LAYOUT.get('screen') or {'x': 0, 'y': 0, 'w': 1920, 'h': 1080}
        zid = f'zr{self.nzoom}'
        self.nzoom += 1
        px, py = cx * 1920 - r['x'], cy * 1080 - r['y']
        self.zooms.append(f'''<div id="{zid}" class="zr" style="left:{r['x']}px;top:{r['y']}px;width:{r['w']}px;height:{r['h']}px">
<div id="{zid}-i" class="zi" style="left:{-r['x']}px;top:{-r['y']}px"><video id="{zid}-v" src="bg.mp4" muted playsinline data-start="0" data-media-start="0" data-duration="{self.dur}" data-track-index="{5+self.nzoom}"></video></div></div>''')
        a, b = self.L(t0), self.L(t1)
        ox, oy = px + r['x'], py + r['y']
        self.js.append(f"gsap.set('#{zid}-i',{{transformOrigin:'{ox}px {oy}px'}});")
        self.js.append(f"tl.set('#{zid}',{{opacity:1}},{a});")
        # Verschiebung so begrenzen, dass das skalierte Bild die Region immer ganz füllt
        def clamp(o, size, r0, rlen):
            want = (r0 + rlen / 2) - o
            lo = (r0 + rlen) - (o + (size - o) * scale)   # rechter/unterer Rand muss Region decken
            hi = r0 - (o - o * scale)                      # linker/oberer Rand muss Region decken
            return max(lo, min(hi, want))
        tx, ty = clamp(ox, 1920, r['x'], r['w']), clamp(oy, 1080, r['y'], r['h'])
        self.js.append(f"tl.fromTo('#{zid}-i',{{scale:1,x:0,y:0}},{{scale:{scale},x:{tx:.1f},y:{ty:.1f},duration:{ease_in},ease:'power3.inOut'}},{a});")
        self.js.append(f"tl.to('#{zid}-i',{{scale:1,x:0,y:0,duration:{ease_in},ease:'power3.inOut'}},{q(b-ease_in)});")
        self.js.append(f"tl.set('#{zid}',{{opacity:0}},{b});")
        cam = LAYOUT.get('cam')
        if cam and cam['shape'] == 'circle':
            self.cam = True    # runde Facecam liegt im Bildschirmbereich → scharf obendrauf

    # ───────── Einblendungen ─────────
    # Clean-Stil (aus Feedback „sieht zu sehr nach KI aus, zu viele Kacheln, zu viele Schriften“):
    # Standard ist freier Text direkt im Bild – nur die Profilschrift, Headlines 600 mit −0,04 em, Fließtext 400/600,
    # dahinter ein weicher Schatten (im Bildschirmteil zusätzlich ein weich auslaufender Blur). Keine Glaskacheln,
    # keine 3D-Icons in Texteinblendungen. box=True legt bei sehr unruhigem Hintergrund eine schlichte dunkle Fläche
    # dahinter (ohne Icon, ohne Lichtkante). Einstieg: Wörter steigen nacheinander mit Unschärfe ein.

    def _block(self, cid, pos, w, inner, blur=None, box=False, align='left', shade=None):
        """Textblock ohne Kachel. blur=None → im Bildschirm-/Split-Teil an, im Talking Head aus."""
        bl = (self.kind != 'th') if blur is None else blur
        sa = shade if shade is not None else (.5 if bl else .3)
        bg = '<i class="pn"></i>' if box else f'<i class="sc" style="--sa:{sa}"></i>' + ('<i class="sb"></i>' if bl else '')
        wcss = f'width:{w}px;' if w else ''
        self.layers.append(f'<div id="{cid}" class="card" style="{pos_css(pos)};{wcss}text-align:{align}">{bg}<div class="ct">{inner}</div></div>')

    def _reveal(self, cid, t0, t1, items=(), sfx=None, gain=0.12):
        """Einstieg/Ausstieg eines _block: Schatten blendet weich auf, Label → Headline Wort für Wort → Rest."""
        a, b = self.L(t0), self.L(t1)
        self.cues.append(t0)
        html = self.layers[-1]
        bg = f"'#{cid} .sc, #{cid} .sb, #{cid} .pn'"
        self.js.append(f"tl.fromTo('#{cid}',{{opacity:0}},{{opacity:1,duration:.01}},{a});")
        self.js.append(f"tl.fromTo({bg},{{opacity:0}},{{opacity:1,duration:.8,ease:'power2.out'}},{a});")
        if 'class="rv0' in html:
            self.js.append(f"tl.fromTo('#{cid} .rv0',{{opacity:0,y:10,filter:'blur(6px)'}},{{opacity:1,y:0,filter:'blur(0px)',duration:.7,ease:'power3.out'}},{a});")
        if 'class="w' in html:
            self.js.append(f"tl.fromTo('#{cid} .w',{{opacity:0,y:22,filter:'blur(10px)'}},{{opacity:1,y:0,filter:'blur(0px)',duration:.85,ease:'power3.out',stagger:.055}},{q(a+0.08)});")
        if 'class="rv ' in html or 'class="rv"' in html:
            self.js.append(f"tl.fromTo('#{cid} .rv',{{opacity:0,y:14,filter:'blur(6px)'}},{{opacity:1,y:0,filter:'blur(0px)',duration:.8,ease:'power3.out',stagger:.12}},{q(a+0.4)});")
        for j, t in enumerate(items):
            self.js.append(f"tl.fromTo('#{cid}-i{j}',{{opacity:0,y:14,filter:'blur(6px)'}},{{opacity:1,y:0,filter:'blur(0px)',duration:.7,ease:'power3.out'}},{self.L(t)});")
        self.js.append(f"tl.to('#{cid} .ct',{{opacity:0,y:-8,filter:'blur(6px)',duration:.5,ease:'power2.in'}},{q(b-0.5)});")
        self.js.append(f"tl.to({bg},{{opacity:0,duration:.5,ease:'power2.in'}},{q(b-0.5)});")
        self.js.append(f"tl.to('#{cid}',{{opacity:0,duration:.01}},{q(b-0.01)});")
        if sfx:
            self.sfx.append((t0, sfx, gain))

    def _enter_exit(self, cid, t0, t1, frm="{opacity:0,y:24}", to="{opacity:1,y:0}", sfx=None, gain=0.12):
        """Einfacher Ein-/Ausstieg für Elemente ohne Hintergrund-Blur (Mockups, Pillen, eigene raw-Bausteine)."""
        a, b = self.L(t0), self.L(t1)
        self.cues.append(t0)
        self.js.append(f"tl.fromTo('#{cid}',{frm},{{...{to},duration:.9,ease:'power3.out'}},{a});")
        self.js.append(f"tl.to('#{cid}',{{opacity:0,y:-10,duration:.5,ease:'power2.in'}},{q(b-0.5)});")
        if sfx:
            self.sfx.append((t0, sfx, gain))

    def _items(self, cid, times, num=False):
        """(Altlast für eigene raw-Bausteine) Punkte stehen gedimmt bereit und leuchten beim Aussprechen auf."""
        for j, t in enumerate(times):
            self.js.append(f"tl.fromTo('#{cid}-i{j}',{{opacity:.26,x:0}},{{opacity:1,x:8,duration:.5,ease:'power3.out'}},{self.L(t)});")
            self.js.append(f"tl.to('#{cid}-i{j}',{{x:0,duration:.6,ease:'power2.inOut'}},{q(self.L(t)+0.5)});")

    @staticmethod
    def _lbl(kicker):
        return f'<div class="rv0 lbl sh">{H.escape(kicker)}</div>' if kicker else ''

    def tile(self, cid, t0, t1, pos, kicker, title, sub=None, icon=None, light=False, w=600, size=54, box=False,
             blur=None, align='left'):
        """Headline (+ Label darüber, + Unterzeile) frei im Bild. icon/light werden ignoriert (keine Kacheln mehr)."""
        sb = f'<div class="rv tx sh" style="font-size:{max(28, int(size * .56))}px;margin-top:14px">{rich(sub)}</div>' if sub else ''
        self._block(cid, pos, w, f'{self._lbl(kicker)}<div class="hl sh" style="font-size:{size}px">{words(title)}</div>{sb}',
                    blur, box, align)
        self._reveal(cid, t0, t1)

    def listcard(self, cid, t0, t1, pos, kicker, title, items, w=640, light=False, icons=None, isize=40, num=False,
                 box=False, blur=None, align='left'):
        """Aufzählung als Text untereinander: items = [(Ausgabezeit, Text), …] – jeder Punkt erscheint, wenn er
        gesagt wird. num=True setzt eine dezente Nummer davor. icons werden ignoriert."""
        rows = []
        for j, (t, txt) in enumerate(items):
            n = f'<span style="font-weight:400;color:rgba({RGB["papier"]},.55);margin-right:18px">{j+1:02d}</span>' if num else ''
            rows.append(f'<div id="{cid}-i{j}" class="li sh" style="font-size:{isize}px;padding:8px 0;opacity:0">{n}{rich(txt)}</div>')
        ttl = f'<div class="hl sh" style="font-size:{int(isize * 1.35)}px;margin-bottom:14px">{words(title)}</div>' if title else ''
        self._block(cid, pos, w, self._lbl(kicker) + ttl + ''.join(rows), blur, box, align)
        self._reveal(cid, t0, t1, items=[t for t, _ in items])

    def chips(self, cid, t0, t1, pos, kicker, items, w=600, align='flex-start', row=False, size=40, blur=None, box=False):
        """Begriffe (Tools, Nischen …), die nacheinander erscheinen – untereinander (Standard) oder mit row=True als
        Zeile mit „·“ dazwischen. Keine Pillen mehr."""
        ta = {'flex-start': 'left', 'center': 'center', 'flex-end': 'right'}.get(align, 'left')
        if row:
            sep = '<span style="font-weight:400;opacity:.5;margin-right:22px">·</span>'
            cs = ''.join(f'<span id="{cid}-i{j}" class="li sh" style="display:inline-block;opacity:0;margin-right:22px">'
                         f'{sep if j else ""}{rich(txt)}</span>' for j, (_, txt) in enumerate(items))
            body = f'<div style="font-size:{size}px;line-height:1.5">{cs}</div>'
        else:
            body = ''.join(f'<div id="{cid}-i{j}" class="li sh" style="font-size:{size}px;padding:6px 0;opacity:0">{rich(txt)}</div>'
                           for j, (_, txt) in enumerate(items))
        self._block(cid, pos, w, self._lbl(kicker) + body, blur, box, ta)
        self._reveal(cid, t0, t1, items=[t for t, _ in items])

    def search(self, cid, t0, t1, pos, kicker, queries, w=700, blur=None):
        """Getippte Suchleisten (z. B. Google-Maps-Suchen) – schlichte dunkle Suchpille, Label frei darüber."""
        lines = []
        for j, (t, txt) in enumerate(queries):
            chars = ''.join(f'<span class="ch">{H.escape(c) if c != " " else "&nbsp;"}</span>' for c in txt)
            lines.append(f'<div id="{cid}-q{j}" style="opacity:0;margin-top:14px;border-radius:100px;padding:20px 30px;display:flex;align-items:center;gap:18px;font-size:30px;font-weight:400;letter-spacing:-.02em;background:rgba({RGB["basis"]},.78);-webkit-backdrop-filter:blur(24px);backdrop-filter:blur(24px)"><span style="display:flex;opacity:.7">{SEARCH}</span><span id="{cid}-t{j}">{chars}</span></div>')
        self._block(cid, pos, w, self._lbl(kicker) + ''.join(lines), blur)
        self._reveal(cid, t0, t1)
        for j, (t, txt) in enumerate(queries):
            lt = self.L(t)
            self.js.append(f"tl.fromTo('#{cid}-q{j}',{{opacity:0,y:12}},{{opacity:1,y:0,duration:.6,ease:'power3.out'}},{lt});")
            self.js.append(f"tl.fromTo('#{cid}-t{j} .ch',{{opacity:0}},{{opacity:1,duration:.01,stagger:.045}},{q(lt+0.15)});")
            self.sfx.append((t, 'typing', 0.10))

    def learning(self, cid, t0, t1, n, text, icon=None, face=None):
        """Kern-Takeaway: Hintergrund abgedunkelt und geblurrt, große Headline frei im Bild, Kamera bleibt scharf.

        Im Vollbild-Talking-Head ('th', auch Kamera-Einschübe): die Person scharf im 9:16-Rahmen links, Text daneben,
        beides vertikal mittig. icon wird ignoriert.
        """
        if self.kind == 'th':
            return self._learning_th(cid, t0, t1, n, text, face or getattr(self, 'face', None))
        self.layers.append(f'<div id="{cid}-dim" class="dim" style="background:rgba({RGB["basis"]},.52);-webkit-backdrop-filter:blur(18px);backdrop-filter:blur(18px)"></div>')
        x0, x1 = free_x()
        w = min(1150, x1 - x0 - 120)
        self.layers.append(f'''<div style="position:absolute;left:{int(x0 + (x1 - x0 - w) / 2)}px;top:0;width:{w}px;height:1080px;display:flex;align-items:center">
<div id="{cid}" class="card" style="position:relative"><div class="ct">{self._lbl(T['learning'].format(n=n))}<div class="hl sh" style="font-size:84px">{words(text)}</div></div></div></div>''')
        self._dim_inout(cid, t0, t1)
        self._reveal(cid, t0 + 0.15, t1, sfx='whoosh-cinematic', gain=0.1)

    def _dim_inout(self, cid, t0, t1):
        a, b = self.L(t0), self.L(t1)
        self.js.append(f"tl.fromTo('#{cid}-dim',{{opacity:0}},{{opacity:1,duration:.7,ease:'power2.out'}},{a});tl.to('#{cid}-dim',{{opacity:0,duration:.6}},{q(b-0.6)});")

    def _learning_th(self, cid, t0, t1, n, text, face=None, fw=432, fh=768, fx=130, scale=0.8):
        # Ecken wie die Kamera-Maske der Aufnahmesoftware (aufnahme.rahmen_radius, Standard 6,5 % der Breite)
        rad = round(fw * OBS_RADIUS)
        face = face or LAYOUT.get('face', [0.5, 0.4])
        fy = int((1080 - fh) / 2)
        vw, vh = int(1920 * scale), int(1080 * scale)
        vl = int(fw / 2 - face[0] * 1920 * scale)
        vt = min(0, int(fh * 0.4 - face[1] * 1080 * scale))
        self.layers.append(f'<div id="{cid}-dim" class="dim" style="background:rgba({RGB["basis"]},.5);-webkit-backdrop-filter:blur(22px);backdrop-filter:blur(22px)"></div>')
        self.layers.append(f'''<div id="{cid}-cam" style="position:absolute;left:{fx}px;top:{fy}px;width:{fw}px;height:{fh}px;border-radius:{rad}px;overflow:hidden;opacity:0;box-shadow:0 30px 90px rgba(0,0,0,.5)">
<video id="{cid}-v" src="bg.mp4" muted playsinline data-start="0" data-media-start="0" data-duration="{self.dur}" data-track-index="9" style="position:absolute;left:{vl}px;top:{vt}px;width:{vw}px;height:{vh}px;object-fit:cover"></video></div>''')
        cl = fx + fw + 90
        cw = 1920 - cl - 130
        self.layers.append(f'''<div style="position:absolute;left:{cl}px;top:0;width:{cw}px;height:1080px;display:flex;align-items:center">
<div id="{cid}" class="card" style="position:relative"><div class="ct">{self._lbl(T['learning'].format(n=n))}<div class="hl sh" style="font-size:84px">{words(text)}</div></div></div></div>''')
        a, b = self.L(t0), self.L(t1)
        self._dim_inout(cid, t0, t1)
        self.js.append(f"tl.fromTo('#{cid}-cam',{{opacity:0,x:-40,scale:.97}},{{opacity:1,x:0,scale:1,duration:.9,ease:'power3.out'}},{q(a+0.05)});tl.to('#{cid}-cam',{{opacity:0,x:-20,duration:.5,ease:'power2.in'}},{q(b-0.5)});")
        self._reveal(cid, t0 + 0.2, t1, sfx='whoosh-cinematic', gain=0.1)

    def chapter(self, cid, t0, t1, n, title, icon=None, total=4, pos=None, letterbox=True, label=None):
        """Kapitelstart als Titelkarte: Bild abgedunkelt + geblurrt, Kinobalken oben/unten fahren ein, großer Titel,
        darunter eine feine Fortschrittslinie. Kamera bleibt scharf (liegt über den Balken). icon wird ignoriert."""
        x0, x1 = free_x()
        pos = pos or {'left': max(130, x0 + 60), 'top': 0}
        bars = ('<i id="%s-lb0" style="position:absolute;left:0;top:0;width:1920px;height:130px;background:#000;transform-origin:50%% 0"></i>'
                '<i id="%s-lb1" style="position:absolute;left:0;bottom:0;width:1920px;height:130px;background:#000;transform-origin:50%% 100%%"></i>' % (cid, cid)) if letterbox else ''
        self.layers.append(f'<div id="{cid}-dim" class="dim" style="background:rgba({RGB["basis"]},.42);-webkit-backdrop-filter:blur(16px);backdrop-filter:blur(16px)">{bars}</div>')
        dots = ''.join(f'<i style="display:block;height:3px;width:70px;border-radius:3px;background:rgba({RGB["papier"]},{".95" if k < n else ".22"})"></i>' for k in range(total))
        lab = label or T['schritt'].format(n=f'{n:02d}', total=f'{total:02d}')
        self.layers.append(f'''<div style="position:absolute;left:{pos['left']}px;top:0;width:{min(1100, x1 - pos['left'] - 80)}px;height:1080px;display:flex;align-items:center">
<div id="{cid}" class="card" style="position:relative"><div class="ct">{self._lbl(lab)}<div class="hl sh" style="font-size:104px">{words(title)}</div>
<div class="rv" style="display:flex;gap:10px;margin-top:34px">{dots}</div></div></div></div>''')
        a, b = self.L(t0), self.L(t1)
        self._dim_inout(cid, t0, t1)
        if letterbox:
            self.js.append(f"tl.fromTo(['#{cid}-lb0','#{cid}-lb1'],{{scaleY:0}},{{scaleY:1,duration:.9,ease:'power3.inOut'}},{a});tl.fromTo(['#{cid}-lb0','#{cid}-lb1'],{{scaleY:1}},{{scaleY:0,duration:.7,ease:'power3.inOut',immediateRender:false}},{q(b-0.7)});")
        self._reveal(cid, t0 + 0.25, t1, sfx='whoosh', gain=0.14)

    def tag(self, cid, t0, t1, pos, text, icon=PIN, light=True, pill=False, size=38, blur=None):
        """Kurzer Hinweis/Status als freie Textzeile. pill=True = alte helle Pille (nur wenn es wirklich ein
        UI-artiges Element sein soll)."""
        if pill:
            self.layers.append(f'''<div id="{cid}" class="card glass light" style="{pos_css(pos)};border-radius:100px;padding:16px 30px 16px 20px;display:flex;align-items:center;gap:14px;font-size:28px;font-weight:600;letter-spacing:-.02em;white-space:nowrap">
<div style="width:46px;height:46px;border-radius:50%;background:var(--tinte);color:var(--akzent);display:flex;align-items:center;justify-content:center">{icon}</div>{rich(text)}</div>''')
            self._enter_exit(cid, t0, t1, frm="{opacity:0,y:16}", sfx='pop')
            return
        self._block(cid, pos, None, f'<div class="hl sh" style="font-size:{size}px;white-space:nowrap">{words(text)}</div>', blur)
        self._reveal(cid, t0, t1)

    def quote(self, cid, t0, t1, pos, kicker, text, w=900, size=60, light=False, box=False, blur=None, align='left'):
        """Schlüsselsatz wörtlich – große Headline in Anführungszeichen, frei im Bild."""
        self._block(cid, pos, w, f'{self._lbl(kicker)}<div class="hl sh" style="font-size:{size}px;line-height:1.12">{words(T["zitat_auf"] + text + T["zitat_zu"])}</div>',
                    blur, box, align)
        self._reveal(cid, t0, t1)

    def textbehind(self, cid, t0, t1, kicker, word, y=150, size=280, sub=None, sub_y=None, ticker=True, face=None,
                   speed=200, show_kicker=False):
        """Großes Wort HINTER der Person (nur Vollbild-Talking-Head; braucht Freistellung, macht build.py).

        ticker=True: Das Wort läuft wie ein Laufband langsam von rechts nach links hinter dem Kopf durch – es startet
        rechts neben dem Kopf und endet links davon, so ist jeder Buchstabe einmal frei lesbar.
        Bewusst langsam: Zielgeschwindigkeit `speed` px/s (Standard 200). t1=None → das
        Fenster wird automatisch so lang, dass genau diese Geschwindigkeit herauskommt (tb_window() rechnet es vorab
        aus, für wide_at in th_pushins). Ein festes t1, das schneller als 240 px/s ergibt, löst eine Warnung aus.
        kicker wird nicht angezeigt (ruhiger) – show_kicker=True holt ihn zurück.
        ticker=False: stehendes Wort in der Bildmitte (nur für kurze Wörter bis ~6 Buchstaben).
        """
        if t1 is None:
            t1 = tb_window(t0, word, size, speed)[1]
        self.cutouts.append((cid, self.L(t0), self.L(t1)))
        self.cues += [t0 + 1.5, t0 + (t1 - t0) / 2]
        a, b = self.L(t0), self.L(t1)
        chars = ''.join(f'<span class="tc" style="display:inline-block">{H.escape(ch) if ch != " " else "&nbsp;"}</span>' for ch in word)
        if ticker:
            fx = (face or getattr(self, 'face', None) or LAYOUT.get('face', [0.5, 0.4]))[0] * 1920
            W = text_width(word, size)
            x0, x1 = fx + TB_GAP, fx - TB_GAP - W     # Start: linke Wortkante rechts vom Kopf · Ende: rechte Kante links davon
            v = (x0 - x1) / max(0.1, b - a)
            if v > 240:
                print(f'⚠ {cid}: Laufband {v:.0f} px/s – zu schnell (Ziel ≤ {speed}). t1=None setzen oder Fenster auf {tb_window(0, word, size, speed)[1]:.1f} s verlängern')
            self.inner_vw.append(f'''<div id="{cid}" style="position:absolute;left:0;top:0;width:1920px;height:1080px;opacity:0">
<div id="{cid}-w" class="tb" style="top:{y}px;left:0;width:auto;text-align:left;font-size:{size}px;text-shadow:0 10px 60px rgba(0,0,0,.35)">{chars}</div></div>''')
            if show_kicker and kicker:
                self.layers.append(f'<div id="{cid}-k" class="lbl sh" style="position:absolute;left:80px;top:{max(40, y-60)}px;opacity:0">{H.escape(kicker)}</div>')
                self.js.append(f"tl.fromTo('#{cid}-k',{{opacity:0}},{{opacity:.9,duration:.35}},{a});tl.to('#{cid}-k',{{opacity:0,duration:.4}},{q(b-0.4)});")
            self.js.append(f"tl.fromTo('#{cid}',{{opacity:0}},{{opacity:1,duration:.5}},{a});")
            self.js.append(f"tl.fromTo('#{cid}-w',{{x:{x0:.0f}}},{{x:{x1:.0f},duration:{q(b-a)},ease:'none'}},{a});")
            self.js.append(f"tl.fromTo('#{cid}-w .tc',{{y:90,opacity:0,filter:'blur(14px)'}},{{y:0,opacity:1,filter:'blur(0px)',duration:1.1,ease:'power3.out',stagger:.05}},{a});")
        else:
            self.inner_vw.append(f'''<div id="{cid}" style="position:absolute;left:0;top:0;width:1920px;height:1080px;opacity:0">
<div id="{cid}-w" class="tb" style="top:{y}px;font-size:{size}px;text-shadow:0 10px 60px rgba(0,0,0,.35)">{chars}</div></div>''')
            self.js.append(f"tl.fromTo('#{cid}',{{opacity:0}},{{opacity:1,duration:.5}},{a});")
            self.js.append(f"tl.fromTo('#{cid}-w .tc',{{y:90,opacity:0,filter:'blur(14px)'}},{{y:0,opacity:1,filter:'blur(0px)',duration:1.1,ease:'power3.out',stagger:.05}},{a});")
            self.js.append(f"tl.fromTo('#{cid}-w',{{scale:.97}},{{scale:1.01,duration:{q(b-a)},ease:'none'}},{a});")
        self.js.append(f"tl.to('#{cid}',{{opacity:0,duration:.6}},{q(b-0.6)});")
        self.sfx.append((t0, 'whoosh-cinematic', 0.14))
        if sub:
            sid = cid + '-s'
            self.layers.append(f'<div id="{sid}" class="card hl sh" style="left:160px;top:{sub_y or 800}px;width:1600px;text-align:center;font-size:58px">{words(sub)}</div>')
            self.js.append(f"tl.fromTo('#{sid}',{{opacity:0}},{{opacity:1,duration:.01}},{q(a+0.4)});")
            self.js.append(f"tl.fromTo('#{sid} .w',{{opacity:0,y:18,filter:'blur(8px)'}},{{opacity:1,y:0,filter:'blur(0px)',duration:.85,ease:'power3.out',stagger:.06}},{q(a+0.4)});tl.to('#{sid}',{{opacity:0,duration:.5}},{q(b-0.5)});")

    def subscribe(self, cid, t0, pos=None, channel=None, sub_label=None, avatar=None, dur=6.2):
        """Abo-Störer: Kanal-Pille, Mauszeiger klickt 'Abonnieren' → 'Abonniert ✓', dann klingelt die Glocke.

        Kanalname, Handle und Kanalbild kommen aus dem Profil (kanal.*). Ohne Kanalbild: Initialen im Markenkreis.
        Dauer ≈ 6 s. Braucht kein gesprochenes Stichwort – an eine ruhige Stelle legen (keine andere Karte).
        Die Pille bleibt eine Fläche, weil sie ein echtes UI-Objekt nachbildet.
        """
        pos = pos or CFG.get('subscribe_pos', {'left': 80, 'top': 860})
        channel = channel or PR.get('kanal.name') or 'Kanalname'
        sub_label = sub_label or PR.get('kanal.handle') or ''
        avatar = avatar or PR.get('kanal.avatar')
        if avatar and PR.pfile(avatar):
            av = f'<img src="{os.path.basename(avatar)}" style="width:76px;height:76px;border-radius:50%;object-fit:cover;flex:none">'
        else:
            ini = ''.join(w[0] for w in channel.split()[:2]).upper()
            av = (f'<div style="width:76px;height:76px;border-radius:50%;flex:none;background:linear-gradient(150deg,var(--marke2),var(--marke1));'
                  f'color:var(--papier);display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:600">{H.escape(ini)}</div>')
        c = cid
        self.layers.append(f'''<div id="{c}" class="card glass light" style="{pos_css(pos)};border-radius:100px;padding:14px 16px 14px 14px;display:flex;align-items:center;gap:18px">
{av}
<div style="width:230px;flex:none;white-space:nowrap;overflow:hidden"><div style="font-size:26px;font-weight:600;letter-spacing:-.02em;line-height:1.1">{H.escape(channel)}</div><div style="font-size:18px;opacity:.6;margin-top:3px">{H.escape(sub_label)}</div></div>
<div class="sb-btn" style="width:230px">
 <div id="{c}-a" style="position:absolute;inset:0;border-radius:100px;background:var(--tinte);color:#fff;display:flex;align-items:center;justify-content:center">{H.escape(T["abonnieren"])}</div>
 <div id="{c}-b" style="position:absolute;inset:0;border-radius:100px;background:var(--akzent);color:var(--tinte);display:flex;align-items:center;justify-content:center;gap:10px;opacity:0">{CHECK}<span>{H.escape(T["abonniert"])}</span></div>
 <div id="{c}-r" style="position:absolute;left:50%;top:50%;width:40px;height:40px;margin:-20px 0 0 -20px;border-radius:50%;background:rgba(255,255,255,.55);opacity:0"></div>
</div>
<div id="{c}-bell" style="position:relative;width:64px;height:64px;border-radius:50%;background:rgba({RGB["tinte"]},.07);display:flex;align-items:center;justify-content:center;color:var(--tinte)">
 <div id="{c}-bi" style="display:flex;transform-origin:50% 8%">{BELL}</div>
 <div id="{c}-dot" style="position:absolute;right:12px;top:12px;width:14px;height:14px;border-radius:50%;background:var(--marke2);border:2px solid #fff;opacity:0"></div>
</div>
<div id="{c}-cur" style="position:absolute;left:0;top:0;opacity:0;filter:drop-shadow(0 6px 10px rgba(0,0,0,.35))">{CURSOR}</div>
</div>''')
        a = self.L(t0)
        e = q(a + dur)
        # Positionen relativ zur Pille: Button-Mitte ≈ x 76+18+~190+18+115, Glocke rechts daneben
        # feste Geometrie: Rand 14 + Bild 76 + Abstand 18 + Name 230 + 18 → Button 356–586, Glocke 604–668; Zeigerspitze bei (+11, +7)
        bx, by, gx = 460, 45, 625
        self.js += [
            f"tl.fromTo('#{c}',{{opacity:0,y:40,scale:.94}},{{opacity:1,y:0,scale:1,duration:.8,ease:'expo.out'}},{a});",
            f"tl.fromTo('#{c}-cur',{{opacity:0,x:{bx+260},y:{by+140}}},{{opacity:1,x:{bx},y:{by},duration:.9,ease:'power3.out'}},{q(a+0.7)});",
            f"tl.to('#{c}-cur',{{scale:.82,duration:.09,yoyo:true,repeat:1}},{q(a+1.65)});",
            f"tl.to('#{c} .sb-btn',{{scale:.94,duration:.09,yoyo:true,repeat:1}},{q(a+1.65)});",
            f"tl.fromTo('#{c}-r',{{opacity:.8,scale:.2}},{{opacity:0,scale:6,duration:.6,ease:'power2.out'}},{q(a+1.7)});",
            f"tl.to('#{c}-a',{{opacity:0,duration:.2}},{q(a+1.75)});",
            f"tl.fromTo('#{c}-b',{{opacity:0,scale:.9}},{{opacity:1,scale:1,duration:.4,ease:'back.out(2)'}},{q(a+1.75)});",
            f"tl.to('#{c}-cur',{{x:{gx},y:{by-2},duration:.6,ease:'power3.inOut'}},{q(a+2.3)});",
            f"tl.to('#{c}-cur',{{scale:.82,duration:.09,yoyo:true,repeat:1}},{q(a+3.0)});",
            f"tl.to('#{c}-bell',{{backgroundColor:'rgba({RGB['akzent']},1)',duration:.25}},{q(a+3.05)});",
            f"tl.fromTo('#{c}-dot',{{opacity:0,scale:0}},{{opacity:1,scale:1,duration:.35,ease:'back.out(3)'}},{q(a+3.1)});",
            f"tl.fromTo('#{c}-bi',{{rotation:0}},{{rotation:16,duration:.09,yoyo:true,repeat:7,ease:'sine.inOut'}},{q(a+3.05)});",
            f"tl.set('#{c}-bi',{{rotation:0}},{q(a+3.8)});",
            f"tl.to('#{c}-cur',{{opacity:0,x:{gx+80},y:{by+90},duration:.5,ease:'power2.in'}},{q(a+3.9)});",
            f"tl.to('#{c}',{{opacity:0,y:20,duration:.5,ease:'power2.in'}},{q(e-0.5)});",
        ]
        self.sfx += [(t0, 'whoosh-short', 0.2), (t0 + 1.65, 'click', 0.35), (t0 + 3.0, 'click-soft', 0.3), (t0 + 3.1, 'ping', 0.22)]

    def community(self, cid, t0, t1, bullets, pill_at=None, image='cta.jpg', browser_pos=None, text_pos=None,
                  title=None, bw=960, tw=640, nodim=False):
        """Große CTA-Einblendung: Browserfenster mit Screenshot der CTA-Seite + Vorteile als Textzeilen + Akzent-Pille.

        Texte aus profil.cta (label, titel, pille, anzeige). Screenshot vorher frisch aufnehmen:
        node $SK/scripts/shots.mjs <cta.screenshot_url> cta  → <Arbeitsordner>/assets/cta.jpg
        bullets = [(Ausgabezeit, Text), …]; pill_at = Zeitpunkt, an dem der Link erwähnt wird.
        Standardpositionen lassen eine runde Facecam unten rechts frei; bei anderem Layout Positionen übergeben.
        nodim=True: Hintergrund nicht abdunkeln (z. B. im Vollbild-Talking-Head, damit die Person sichtbar bleibt).
        """
        cta = CTA
        bp = browser_pos or {'left': 80, 'top': 170}
        tp = text_pos or {'left': 1110, 'top': 150}
        rows = ''.join(f'<div id="{cid}-i{j}" class="li sh" style="padding:7px 0;font-size:30px;opacity:0">{rich(t)}</div>' for j, (_, t) in enumerate(bullets))
        if not nodim:
            self.layers.append(f'<div id="{cid}-dim" class="dim" style="background:rgba({RGB["basis"]},.5);-webkit-backdrop-filter:blur(16px);backdrop-filter:blur(16px)"></div>')
        self.layers.append(f'''<div id="{cid}-br" class="card" style="{pos_css(bp)};width:{bw}px;overflow:hidden;border-radius:18px;background:#1b1d1c;box-shadow:0 40px 120px rgba(0,0,0,.55)">
<div style="height:46px;display:flex;align-items:center;gap:9px;padding:0 20px"><i style="width:12px;height:12px;border-radius:50%;background:rgba(255,255,255,.22)"></i><i style="width:12px;height:12px;border-radius:50%;background:rgba(255,255,255,.22)"></i><i style="width:12px;height:12px;border-radius:50%;background:rgba(255,255,255,.22)"></i>
<div style="margin-left:18px;flex:1;height:28px;border-radius:100px;background:rgba(255,255,255,.08);font-size:15px;display:flex;align-items:center;padding-left:16px;color:rgba(255,255,255,.7)">{H.escape(cta.get('anzeige', ''))}</div></div>
<div style="height:{int(bw*0.594)}px;overflow:hidden;position:relative"><img id="{cid}-img" src="{image}" style="position:absolute;left:0;top:0;width:{bw}px"></div></div>
<div id="{cid}-tx" class="card" style="{pos_css(tp)};width:{tw}px"><div class="ct">
{self._lbl(cta.get('label', ''))}
<div class="hl sh" style="font-size:60px;margin-bottom:20px">{words(title or cta.get('titel', ''))}</div>
<div>{rows}</div>
<div id="{cid}-pill" class="pill" style="margin-top:30px;opacity:0">{H.escape(cta.get('pille') or T['link_beschreibung'])}<span class="arr">{ARROW_DOWN}</span></div></div></div>''')
        a, b = self.L(t0), self.L(t1)
        self.cues.append(t0)
        pa = self.L(pill_at if pill_at else t0 + 2.5)
        if not nodim:
            self.js += [f"tl.fromTo('#{cid}-dim',{{opacity:0}},{{opacity:1,duration:.7}},{a});tl.to('#{cid}-dim',{{opacity:0,duration:.5}},{q(b-0.5)});"]
        self.js += [f"tl.fromTo('#{cid}-br',{{opacity:0,y:30,scale:.98}},{{opacity:1,y:0,scale:1,duration:1.1,ease:'power3.out'}},{a});",
                    f"tl.fromTo('#{cid}-tx',{{opacity:0}},{{opacity:1,duration:.01}},{q(a+0.2)});",
                    f"tl.fromTo('#{cid}-tx .rv0',{{opacity:0,y:10,filter:'blur(6px)'}},{{opacity:1,y:0,filter:'blur(0px)',duration:.7,ease:'power3.out'}},{q(a+0.2)});",
                    f"tl.fromTo('#{cid}-tx .w',{{opacity:0,y:22,filter:'blur(10px)'}},{{opacity:1,y:0,filter:'blur(0px)',duration:.85,ease:'power3.out',stagger:.055}},{q(a+0.3)});",
                    f"tl.fromTo('#{cid}-img',{{scale:1,y:0}},{{scale:1.05,y:-12,duration:{q(b-a)},ease:'none'}},{a});",
                    f"tl.fromTo('#{cid}-pill',{{opacity:0,y:16}},{{opacity:1,y:0,duration:.8,ease:'power3.out'}},{pa});",
                    f"tl.to(['#{cid}-br','#{cid}-tx'],{{opacity:0,y:-12,duration:.5,ease:'power2.in'}},{q(b-0.5)});"]
        self.js += [f"tl.fromTo('#{cid}-i{j}',{{opacity:0,y:14,filter:'blur(6px)'}},{{opacity:1,y:0,filter:'blur(0px)',duration:.7,ease:'power3.out'}},{self.L(t)});" for j, (t, _) in enumerate(bullets)]
        self.sfx += [(t0, 'whoosh', 0.18), ((pill_at or t0 + 2.5), 'pop', 0.14)]

    def outro_cta(self, cid, t0, pos=None, image='cta.jpg'):
        """CTA im Outro: Screenshot im schlichten Rahmen, darunter Headline + Akzent-Pille (bleibt bis Segmentende).
        Texte aus profil.cta (label, outro_titel oder titel, pille)."""
        cta = CTA
        pos = pos or {'left': 1230, 'top': 200}
        self.layers.append(f'''<div id="{cid}" class="card" style="{pos_css(pos)};width:600px"><i class="sc" style="--sa:.4"></i><div class="ct">
<img class="rv0" src="{image}" style="display:block;width:600px;height:300px;object-fit:cover;object-position:0 0;border-radius:16px;box-shadow:0 30px 90px rgba(0,0,0,.5)">
<div style="margin-top:34px">{self._lbl(cta.get('label', ''))}</div>
<div class="hl sh" style="font-size:54px;margin-bottom:26px">{words(cta.get('outro_titel') or cta.get('titel', ''))}</div>
<div class="rv pill" style="font-size:22px">{H.escape(cta.get('pille') or T['link_beschreibung'])}<span class="arr">{ARROW_DOWN}</span></div></div></div>''')
        self._reveal(cid, t0, self.t0 + self.dur - 0.05, sfx='whoosh', gain=0.16)

    def before_after(self, cid, switches, top=96):
        """'Vorher' / 'Nachher' als schlichtes Textlabel, das an den Umschaltpunkten wechselt. switches = [(Ausgabezeit, 0|1), …]."""
        self.layers.append(f'''<div id="{cid}" class="card" style="left:760px;top:{top}px;width:400px;display:flex;justify-content:center;opacity:1">
<div style="position:relative;width:400px;height:60px">
<div id="{cid}0" class="hl sh" style="position:absolute;inset:0;text-align:center;font-size:40px;opacity:0;color:rgba({RGB["papier"]},.75)">{H.escape(T["vorher"])}</div>
<div id="{cid}1" class="hl sh" style="position:absolute;inset:0;text-align:center;font-size:40px;opacity:0">{H.escape(T["nachher"])}</div></div></div>''')
        for t, st in switches:
            self.js.append(f"tl.to('#{cid}{1-st}',{{opacity:0,duration:.25}},{self.L(t)});tl.fromTo('#{cid}{st}',{{opacity:0,y:10,filter:'blur(6px)'}},{{opacity:1,y:0,filter:'blur(0px)',duration:.5,ease:'power3.out'}},{self.L(t)});")
        self.js.append(f"tl.to('#{cid}',{{opacity:0,duration:.4}},{q(self.dur-0.45)});")

    def compare(self, cid, t0, t1, pos, kicker, title, bars, icon=None, w=700, box=False, blur=None):
        """Balkenvergleich, frei im Bild. bars = [(Ausgabezeit, Label, Wert 0–100, Farbe, Wertlabel), …];
        Farbe z. B. 'var(--aqua)' oder '#faf6f3'. icon wird ignoriert. Balken wachsen per scaleX (kein width)."""
        rows = ''.join(f'''<div id="{cid}-i{j}" style="margin-top:24px;opacity:0"><div class="li sh" style="display:flex;justify-content:space-between;font-size:32px"><span>{rich(lab)}</span><span style="font-weight:400;opacity:.75">{H.escape(vl)}</span></div>
<div style="height:6px;border-radius:6px;background:rgba(255,255,255,.14);margin-top:12px;overflow:hidden"><div id="{cid}-b{j}" style="height:6px;width:{v}%;border-radius:6px;background:{col};transform-origin:0 50%;transform:scaleX(0)"></div></div></div>''' for j, (_, lab, v, col, vl) in enumerate(bars))
        ttl = f'<div class="hl sh" style="font-size:46px">{words(title)}</div>' if title else ''
        self._block(cid, pos, w, self._lbl(kicker) + ttl + rows, blur, box)
        self._reveal(cid, t0, t1, items=[t for t, *_ in bars])
        for j, (t, *_) in enumerate(bars):
            self.js.append(f"tl.fromTo('#{cid}-b{j}',{{scaleX:0}},{{scaleX:1,duration:1.4,ease:'power3.out'}},{q(self.L(t)+0.2)});")

    def sponsor(self, cid, t0, t1, type_at=None, headline=None, footer=None, mode=None, char_dt=0.085):
        """Werbepartner-Einblendung (bezahlte Kooperation): weiße Fläche, Partner-Logo, Rabattcode wird
        groß in ein Gutscheinfeld getippt, danach „Code angewendet“, darunter Link-Hinweis.

        Daten aus project.json → sponsor (siehe _load_sponsor). type_at = Ausgabezeit, ab der getippt wird (Standard t0+1,0;
        am besten, wenn der Code ausgesprochen wird). mode: 'panel' = weiße Fläche exakt über dem Bildschirmbereich (Split,
        Kamera bleibt wie sie ist), 'full' = weißer Vollbild-Hintergrund mit der Person scharf im 9:16-Rahmen links (Talking Head).
        Standard: 'full' in th-Segmenten, sonst 'panel'. Standzeit ≥ 7 s, damit der Code gelesen werden kann.
        """
        sp = SPONSOR
        assert sp, 'project.json braucht "sponsor": "<partner>" (Ordner assets/partner/<partner>)'
        mode = mode or ('full' if self.kind == 'th' else 'panel')
        col, soft = sp.get('color', F['marke2']), sp.get('color_soft', '#F4F4F6')
        code = sp['code']
        ink, mut = '#1d1e20', '#6d6a80'
        a, b = self.L(t0), self.L(t1)
        self.cues += [t0 + 0.8, (type_at or t0 + 1.0) + len(code) * char_dt + 0.8, t1 - 1.0]
        if mode == 'full':
            fw, fh, fx = 432, 768, 130
            self.layers.append(f'<div id="{cid}-bg" style="position:absolute;inset:0;background:#fff;opacity:0"></div>')
            face = getattr(self, 'face', None) or LAYOUT.get('face', [0.5, 0.4])
            rad = round(fw * OBS_RADIUS)
            fy = int((1080 - fh) / 2)
            sc = 0.8
            vl = int(fw / 2 - face[0] * 1920 * sc)
            vt = min(0, int(fh * 0.4 - face[1] * 1080 * sc))
            self.layers.append(
                f'<div id="{cid}-cam" style="position:absolute;left:{fx}px;top:{fy}px;width:{fw}px;height:{fh}px;border-radius:{rad}px;'
                f'overflow:hidden;opacity:0;box-shadow:0 30px 80px rgba(40,30,90,.22)">'
                f'<video id="{cid}-v" src="bg.mp4" muted playsinline data-start="0" data-media-start="0" data-duration="{self.dur}" '
                f'data-track-index="9" style="position:absolute;left:{vl}px;top:{vt}px;width:{int(1920*sc)}px;height:{int(1080*sc)}px;'
                f'object-fit:cover"></video></div>')
            px, py = fx + fw + 60, 0
            pw, ph = 1920 - px - 70, 1080
        else:
            scr = LAYOUT.get('screen', {'x': 0, 'y': 0, 'w': 1920, 'h': 1080})
            px, py, pw, ph = scr['x'], scr['y'], scr['w'], scr['h']
            prad = 0 if pw >= 1900 else round(min(pw, ph) * OBS_RADIUS)
            self.layers.append(f'<div id="{cid}-bg" style="position:absolute;left:{px}px;top:{py}px;width:{pw}px;height:{ph}px;'
                               f'border-radius:{prad}px;background:#fff;opacity:0;box-shadow:0 30px 90px rgba(0,0,0,.35)"></div>')
        k = min(1.3, pw / 1000, ph / 680)          # alles skaliert mit der Fläche (plakativ)
        csize = int(118 * k)
        tr = -0.02
        while text_width(code, csize, tr) > pw - 260 * k and csize > 40:
            csize -= 2
        cw = text_width(code, csize, tr)
        xs = [0] + [text_width(code[:i + 1], csize, tr) for i in range(len(code))]
        chars = ''.join(f'<span id="{cid}-c{i}" style="opacity:0">{H.escape(ch)}</span>' for i, ch in enumerate(code))
        hl = headline or sp.get('headline') or T['rabatt'].format(rabatt=sp.get('discount', '10 %'))
        hl_html = ' '.join(
            f'<span class="w" style="display:inline-block;color:{col if w.startswith("*") else ink}">{H.escape(w.strip("*"))}</span>'
            for w in re.findall(r'\*[^*]+\*|\S+', hl))
        ft = footer or sp.get('footer') or T['link_und_code']
        u = lambda v: int(v * k)
        self.layers.append(
            f'<div style="position:absolute;left:{px}px;top:{py}px;width:{pw}px;height:{ph}px;display:flex;align-items:center;justify-content:center;pointer-events:none">'
            f'<div id="{cid}" style="opacity:0;display:flex;flex-direction:column;align-items:center;text-align:center;color:{ink}">'
            f'<img id="{cid}-logo" src="{sp["logo"]}" style="width:{u(420)}px;opacity:0">'
            f'<div id="{cid}-hl" style="margin-top:{u(54)}px;font-size:{u(56)}px;font-weight:600;letter-spacing:-.04em;line-height:1.1">{hl_html}</div>'
            f'<div id="{cid}-f" style="position:relative;margin-top:{u(40)}px;padding:{u(22)}px {u(48)}px {u(26)}px;border-radius:{u(30)}px;'
            f'background:{soft};border:{max(2, u(3))}px solid rgba({PR.hex_rgb(col)},.18);opacity:0;text-align:left">'
            f'<div style="font-size:{u(24)}px;font-weight:500;color:{mut};letter-spacing:-.01em;margin-bottom:{u(4)}px">{H.escape(sp.get("code_label") or T["rabattcode"])}</div>'
            f'<div style="position:relative;width:{int(cw) + 4}px;height:{int(csize * 1.18)}px;font-size:{csize}px;font-weight:600;letter-spacing:{tr}em;line-height:1.18;white-space:nowrap">{chars}'
            f'<i id="{cid}-car" style="position:absolute;left:0;top:{int(csize * .14)}px;width:{max(4, u(7))}px;height:{int(csize * .92)}px;border-radius:4px;background:{col};opacity:0"></i></div>'
            f'<div id="{cid}-ok" style="position:absolute;right:{u(-18)}px;top:{u(-22)}px;display:flex;align-items:center;gap:{u(10)}px;'
            f'padding:{u(10)}px {u(20)}px {u(10)}px {u(14)}px;border-radius:100px;background:{col};color:#fff;font-size:{u(24)}px;font-weight:600;'
            f'letter-spacing:-.01em;opacity:0;box-shadow:0 10px 30px rgba({PR.hex_rgb(col)},.35)">{CHECK}<span>{H.escape(sp.get("applied") or T["code_angewendet"])}</span></div></div>'
            f'<div id="{cid}-ft" style="margin-top:{u(40)}px;font-size:{u(30)}px;letter-spacing:-.02em;opacity:0">'
            f'<span style="font-weight:600">{H.escape(sp.get("url_display", ""))}</span>'
            f'<span style="color:{mut};font-weight:400">&nbsp;&nbsp;·&nbsp;&nbsp;{H.escape(ft)}</span></div>'
            f'</div></div>')
        ts = self.L(type_at) if type_at else q(a + 1.0)
        ts = max(ts, q(a + 0.95))
        te = q(ts + len(code) * char_dt)
        js = [f"tl.fromTo('#{cid}-bg',{{opacity:0}},{{opacity:1,duration:.55,ease:'power2.out'}},{a});",
              f"tl.fromTo('#{cid}',{{opacity:0}},{{opacity:1,duration:.01}},{a});",
              f"tl.fromTo('#{cid}-logo',{{opacity:0,y:18,filter:'blur(8px)'}},{{opacity:1,y:0,filter:'blur(0px)',duration:.8,ease:'power3.out'}},{q(a + 0.2)});",
              f"tl.fromTo('#{cid}-hl .w',{{opacity:0,y:22,filter:'blur(10px)'}},{{opacity:1,y:0,filter:'blur(0px)',duration:.85,ease:'power3.out',stagger:.055}},{q(a + 0.35)});",
              f"tl.fromTo('#{cid}-f',{{opacity:0,y:20,scale:.97}},{{opacity:1,y:0,scale:1,duration:.8,ease:'power3.out'}},{q(a + 0.5)});",
              f"tl.fromTo('#{cid}-ft',{{opacity:0,y:12}},{{opacity:1,y:0,duration:.7,ease:'power3.out'}},{q(a + 0.75)});"]
        if mode == 'full':
            js.append(f"tl.fromTo('#{cid}-cam',{{opacity:0,x:-40,scale:.97}},{{opacity:1,x:0,scale:1,duration:.9,ease:'power3.out'}},{q(a + 0.05)});")
        # Cursor: blinkt bis zum Tippen, steht beim Tippen, blinkt danach weiter
        blink1 = max(0, int((ts - a - 0.5) / 0.4) - 1)   # endet vor dem Tippen (sonst Lint overlapping_gsap_tweens)
        js.append(f"tl.fromTo('#{cid}-car',{{opacity:0}},{{opacity:1,duration:.4,ease:'steps(1)',repeat:{blink1},yoyo:true}},{q(a + 0.5)});")
        js.append(f"tl.set('#{cid}-car',{{opacity:1}},{ts});")
        for i in range(len(code)):
            t = q(ts + i * char_dt)
            js.append(f"tl.set('#{cid}-c{i}',{{opacity:1}},{t});tl.set('#{cid}-car',{{x:{xs[i + 1]:.1f}}},{t});")
        ok = q(te + 0.35)
        js += [f"tl.to('#{cid}-f',{{borderColor:'{col}',duration:.3}},{ok});",
               f"tl.fromTo('#{cid}-ok',{{opacity:0,scale:.6,y:8}},{{opacity:1,scale:1,y:0,duration:.5,ease:'back.out(2.2)'}},{ok});"]
        blink2 = max(0, int((b - 0.9 - ok) / 0.45) - 1)
        js.append(f"tl.fromTo('#{cid}-car',{{opacity:1}},{{opacity:0,duration:.45,ease:'steps(1)',repeat:{blink2},yoyo:true,immediateRender:false}},{q(ok + 0.3)});")
        js += [f"tl.to('#{cid}',{{opacity:0,y:-10,filter:'blur(6px)',duration:.5,ease:'power2.in'}},{q(b - 0.5)});",
               f"tl.to('#{cid}-bg',{{opacity:0,duration:.55,ease:'power2.in'}},{q(b - 0.55)});"]
        if mode == 'full':
            js.append(f"tl.to('#{cid}-cam',{{opacity:0,x:-20,duration:.5,ease:'power2.in'}},{q(b - 0.5)});")
        self.js += js
        self.sfx += [(t0, 'whoosh', 0.18), (self.t0 + ts, 'typing', 0.16), (self.t0 + ok, 'pop', 0.2)]

    def sponsor_link(self, cid, t0, t1, pos=None, type_at=None, label=None, char_dt=0.045, size=40):
        """Werbepartner-Link als weiße Pille (Partner-Icon + getippter Link + Pfeil „Beschreibung“), z. B. bei
        „ich blende dir den Link ein“. Standard: unten mittig im Bildschirmbereich (Split) bzw. unten links (Talking Head)."""
        sp = SPONSOR
        assert sp, 'project.json braucht "sponsor"'
        col, ink, mut = sp.get('color', F['marke2']), '#1d1e20', '#6d6a80'
        url = sp.get('url_display', '')
        label = label if label is not None else T['link_beschreibung']
        tr = -0.02
        uw = text_width(url, size, tr)
        lw = text_width(label, 24, -0.01) if label else 0
        est = 18 + 48 + 18 + uw + (24 + lw if label else 0) + 18 + 48 + 14
        if pos is None:
            if self.kind == 'th':
                pos = {'left': 110, 'top': 900}
            else:
                scr = LAYOUT.get('screen', {'x': 0, 'y': 0, 'w': 1920, 'h': 1080})
                pos = {'left': int(scr['x'] + scr['w'] / 2 - est / 2), 'top': int(scr['y'] + scr['h'] - 118)}
        xs = [0] + [text_width(url[:i + 1], size, tr) for i in range(len(url))]
        chars = ''.join(f'<span id="{cid}-c{i}" style="opacity:0">{H.escape(ch)}</span>' for i, ch in enumerate(url))
        lab = (f'<span style="font-size:24px;font-weight:500;color:{mut};letter-spacing:-.01em;white-space:nowrap">{H.escape(label)}</span>'
               if label else '')
        self.layers.append(
            f'<div id="{cid}" style="position:absolute;{pos_css(pos)};opacity:0;display:flex;align-items:center;gap:18px;padding:14px 14px 14px 18px;'
            f'border-radius:100px;background:#fff;box-shadow:0 24px 70px rgba(0,0,0,.35)">'
            f'<img src="{sp.get("icon", sp["logo"])}" style="height:48px;width:auto;flex:none">'
            f'<div style="position:relative;width:{int(uw) + 4}px;height:{int(size * 1.2)}px;font-size:{size}px;font-weight:600;letter-spacing:{tr}em;'
            f'line-height:1.2;color:{ink};white-space:nowrap">{chars}'
            f'<i id="{cid}-car" style="position:absolute;left:0;top:{int(size * .16)}px;width:4px;height:{int(size * .9)}px;border-radius:3px;background:{col};opacity:0"></i></div>'
            f'{lab}<span style="flex:none;width:48px;height:48px;border-radius:50%;background:{col};color:#fff;display:flex;align-items:center;justify-content:center">{ARROW_DOWN}</span></div>')
        a, b = self.L(t0), self.L(t1)
        self.cues += [t0 + 0.6, t1 - 1.0]
        ts = max(self.L(type_at) if type_at else q(a + 0.6), q(a + 0.5))
        js = [f"tl.fromTo('#{cid}',{{opacity:0,y:30,scale:.96}},{{opacity:1,y:0,scale:1,duration:.7,ease:'power3.out'}},{a});",
              f"tl.set('#{cid}-car',{{opacity:1}},{q(a + 0.3)});"]
        for i in range(len(url)):
            t = q(ts + i * char_dt)
            js.append(f"tl.set('#{cid}-c{i}',{{opacity:1}},{t});tl.set('#{cid}-car',{{x:{xs[i + 1]:.1f}}},{t});")
        te = q(ts + len(url) * char_dt + 0.3)
        js.append(f"tl.set('#{cid}-car',{{opacity:0}},{te});")
        js.append(f"tl.to('#{cid}',{{opacity:0,y:14,duration:.5,ease:'power2.in'}},{q(b - 0.5)});")
        self.js += js
        self.sfx += [(t0, 'whoosh-short', 0.16), (self.t0 + ts, 'typing', 0.12)]

    def raw(self, html_layer, js_lines, sfx=()):
        """Freie Komponente (eigenes HTML + GSAP-Zeilen). IDs eindeutig halten."""
        self.layers.append(html_layer)
        self.js.extend(js_lines)
        self.sfx.extend(sfx)

    # ───────── Ausgabe ─────────
    def _layers_with_cam(self, cam):
        last = max(i for i, l in enumerate(self.layers) if 'class="dim"' in l)
        return ''.join(self.layers[:last + 1]) + cam + ''.join(self.layers[last + 1:])

    def html(self):
        cut = ''.join(
            f'<div style="position:absolute;left:0;top:0;width:1920px;height:1080px"><video id="cut_{cid}" src="cut_{cid}.webm" muted playsinline data-start="{a}" data-media-start="0" data-duration="{q(b-a)}" data-track-index="{2+i}"></video></div>'
            for i, (cid, a, b) in enumerate(self.cutouts))
        has_dim = any('class="dim"' in l for l in self.layers) and self.kind != 'end'
        need_cam = (self.cam or has_dim) and LAYOUT.get('cam') and self.kind != 'th'
        cam = (f'<div class="cam"><video id="camv" src="bg.mp4" muted playsinline data-start="0" data-media-start="0" data-duration="{self.dur}" data-track-index="1"></video></div>'
               if need_cam else '')
        body_layers = ''.join(self.zooms) + (self._layers_with_cam(cam) if (has_dim and cam) else cam + ''.join(self.layers))
        return f'''<!doctype html>
<html lang="{PR.get('sprache', 'de')}"><head><meta charset="utf-8"><meta name="viewport" content="width=1920, height=1080">
<style>{FONTS}{CSS}</style><script src="gsap.min.js"></script></head>
<body><div id="root" data-composition-id="{self.id}" data-start="0" data-duration="{self.dur}" data-fps="{FPS}" data-width="1920" data-height="1080">
<div id="vw" class="vw"><video id="bgv" src="bg.mp4" muted playsinline data-start="0" data-media-start="0" data-duration="{self.dur}" data-track-index="0"></video>
{''.join(self.inner_vw)}{cut}</div>
{body_layers}
</div>
<script>
const tl=gsap.timeline({{paused:true}});
{chr(10).join(self.js)}
tl.set({{}},{{}},{self.dur});
window.__timelines["{self.id}"]=tl;
</script></body></html>'''


# ───────── Storyboard-Helfer ─────────
COMPS = []


def comp(cid, src0, src1, kind='sc'):
    """Neues Segment in QUELLZEIT anlegen (src1='end' = bis Videoende). kind: 'th' | 'sc'."""
    c = Comp(cid, S(src0), OUT_DUR if src1 == 'end' else S(src1), kind)
    COMPS.append(c)
    return c


def endcard(seconds=None):
    """Endkarte (wird ans Video angehängt): geblurrtes Schlussbild, Logo, Claim, Pille.

    Inhalt aus dem Profil: marke.logo_hell, cta.claim, cta.endkarte_sub, cta.pille. Ist kein CTA aktiv,
    zeigt die Pille 'Abonnieren' und der Claim den Kanalnamen.
    """
    seconds = seconds or CFG.get('end_card_seconds', 5.0)
    on = CTA.get('aktiv')
    logo = PR.get('marke.logo_hell')
    logo_html = (f'<img id="en-logo" src="{os.path.basename(logo)}" style="width:380px;max-height:200px;object-fit:contain;opacity:0">'
                 if PR.pfile(logo) else '<div id="en-logo"></div>')
    claim = (CTA.get('claim') if on else '') or PR.get('kanal.name') or ''
    sub = CTA.get('endkarte_sub', '') if on else (PR.get('kanal.handle') or '')
    pill = (CTA.get('pille') or T['link_beschreibung']) if on else T['abonnieren']
    c = Comp('end', OUT_DUR, OUT_DUR + seconds, 'end')
    COMPS.append(c)
    c.raw(f'''<div id="en-dim" class="dim" style="background:rgba({RGB['basis']},.62);-webkit-backdrop-filter:blur(34px);backdrop-filter:blur(34px)"></div>
<div id="en" class="card" style="left:0;top:250px;width:1920px;text-align:center;opacity:1">
{logo_html}
<div id="en-t" class="ttl" style="font-size:112px;margin-top:46px;opacity:0">{rich(claim)}</div>
<div id="en-s" class="sub" style="font-size:32px;margin-top:22px;opacity:0">{H.escape(sub)}</div>
<div id="en-p" class="pill" style="margin-top:44px;opacity:0">{H.escape(pill)}<span class="arr">{ARROW_DOWN}</span></div></div>''',
          ["tl.fromTo('#en-dim',{opacity:0},{opacity:1,duration:.9,ease:'power2.out'},0);",
           "tl.fromTo('#en-logo',{opacity:0,y:20},{opacity:1,y:0,duration:.8,ease:'expo.out'},0.3);",
           "tl.fromTo('#en-t',{opacity:0,y:40},{opacity:1,y:0,duration:.9,ease:'expo.out'},0.5);",
           "tl.fromTo('#en-s',{opacity:0,y:20},{opacity:1,y:0,duration:.8,ease:'expo.out'},0.8);",
           "tl.fromTo('#en-p',{opacity:0,y:20,scale:.9},{opacity:1,y:0,scale:1,duration:.7,ease:'back.out(1.8)'},1.1);"],
          sfx=[(OUT_DUR + 0.1, 'whoosh-cinematic', 0.2)])
    return c
