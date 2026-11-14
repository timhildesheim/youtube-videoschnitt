"""Profil fertigstellen – nach dem Einrichtungsinterview (references/einrichtung.md) und nach jeder Profiländerung.

Mit der Python-Umgebung aus check_env.sh ausführen (braucht fonttools):
    ~/.cache/youtube-videoschnitt/mgenv/bin/python $SK/scripts/setup_profil.py [--avatar-von-kanal] [--nur-pruefen]

Was passiert:
  1. Schriften: Die Google-Fonts aus marke.schriften werden in <Profil>/fonts/ geladen (TTF), fonts.css und die
     Glyphenbreiten (breiten.json, fürs Laufband) erzeugt. Eigene Schriftdateien (TTF/OTF) stattdessen einfach in
     <Profil>/fonts/ legen – sie werden dann über ihre Metadaten erkannt (Familie, Stärke, kursiv).
  2. --avatar-von-kanal: Kanalbild (og:image) von kanal.url laden → <Profil>/kanal-avatar.jpg (900×900).
  3. Farben prüfen: Kontrast Pillentext (tinte auf akzent), heller Text auf dunklem Glas, Text auf hellem Glas.
  4. bilder.foto_stil aus den Markenfarben vorbelegen, wenn leer.
"""
import glob, json, os, re, subprocess, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profil as PR

args = sys.argv[1:]
if not PR.EXISTS:
    sys.exit(f'Kein Profil unter {PR.PFILE} – erst das Einrichtungsinterview führen.')
raw = json.load(open(PR.PFILE))
P = PR.P
FD = os.path.join(PR.PDIR, 'fonts')
os.makedirs(FD, exist_ok=True)
CHARS = [chr(c) for c in range(32, 127)] + list('ÄÖÜäöüßéèàáçñ€–—„“”‚‘’…·×')


# ───────── Farben ─────────
def lum(h):
    r, g, b = (int(x) / 255 for x in PR.hex_rgb(h).split(','))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


F = P['marke']['farben']
bad = [k for k, v in F.items() if not re.fullmatch(r'#?[0-9a-fA-F]{6}|#?[0-9a-fA-F]{3}', v or '')]
if bad:
    sys.exit(f'✗ Ungültige Farbwerte: {bad} (Format #rrggbb)')
checks = [('Pillentext (tinte auf akzent)', F['tinte'], F['akzent'], 4.5),
          ('Text im Bild auf Abdunklung (papier auf basis)', F['papier'], F['basis'], 7),
          ('Text auf heller Pille (tinte auf papier)', F['tinte'], F['papier'], 7),
          ('CTA-Pille hebt sich ab (akzent auf basis)', F['akzent'], F['basis'], 3)]
print('Farben:')
for name, a, b, need in checks:
    c = contrast(a, b)
    print(f"  {'✓' if c >= need else '⚠'} {name}: {c:.1f}:1 (Ziel ≥ {need})")
if '--nur-pruefen' in args:
    sys.exit(0)


# ───────── Schriften ─────────
def gf_ttf(family, weight, italic):
    """URL der TTF-Datei bei Google Fonts (ohne Browser-Kennung liefert die API TTF)."""
    fam = family.replace(' ', '+')
    url = f'https://fonts.googleapis.com/css2?family={fam}:ital,wght@{1 if italic else 0},{weight}'
    try:
        css = urllib.request.urlopen(url, timeout=30).read().decode()
    except Exception:
        if italic:
            return None
        try:   # Schriften ohne Kursivachse
            css = urllib.request.urlopen(f'https://fonts.googleapis.com/css2?family={fam}:wght@{weight}', timeout=30).read().decode()
        except Exception:
            return None
    m = re.search(r"src:\s*url\((https://[^)]+)\)", css)
    return m.group(1) if m else None


def download(url, dst):
    with urllib.request.urlopen(url, timeout=60) as r, open(dst, 'wb') as f:
        f.write(r.read())


def font_meta(path):
    from fontTools.ttLib import TTFont
    t = TTFont(path)
    name = t['name']
    fam = (name.getDebugName(16) or name.getDebugName(1) or '').strip()
    w = t['OS/2'].usWeightClass if 'OS/2' in t else 400
    it = bool(t['OS/2'].fsSelection & 1) if 'OS/2' in t else 'italic' in os.path.basename(path).lower()
    return fam, w, it


def widths(path):
    from fontTools.ttLib import TTFont
    t = TTFont(path)
    upm = t['head'].unitsPerEm
    cmap, hmtx = t.getBestCmap(), t['hmtx']
    out = {}
    for ch in CHARS:
        g = cmap.get(ord(ch))
        if g:
            out[ch] = round(hmtx[g][0] / upm, 4)
    return out


sf = P['marke']['schriften']
local = [f for f in glob.glob(os.path.join(FD, '*')) if f.lower().endswith(('.ttf', '.otf'))]
faces = []   # (familie, gewicht, kursiv, datei)
if '--google' not in args and local and not all(os.path.basename(f).startswith('gf_') for f in local):
    print('Schriften: eigene Dateien im Profilordner gefunden')
    for f in local:
        fam, w, it = font_meta(f)
        faces.append((fam, w, it, os.path.basename(f)))
else:
    print('Schriften: lade von Google Fonts …')
    for f in glob.glob(os.path.join(FD, 'gf_*')):
        os.remove(f)
    want = [(sf['text'], w, False) for w in (300, 400, 500, 600, 700)]
    # Der Clean-Stil nutzt nur EINE Schrift. Eine zweite (schriften.akzent) wird nur geladen, wenn sie gesetzt ist –
    # für eigene raw()-Bausteine.
    if sf.get('akzent'):
        want += [(sf['akzent'], 400, sf.get('akzent_kursiv', False)), (sf['akzent'], 400, False)]
    for fam, w, it in want:
        url = gf_ttf(fam, w, it)
        if not url:
            print(f'  • {fam} {w}{" kursiv" if it else ""}: nicht verfügbar')
            continue
        fn = f"gf_{re.sub(r'[^A-Za-z0-9]', '', fam)}-{w}{'-italic' if it else ''}.ttf"
        download(url, os.path.join(FD, fn))
        faces.append((fam, w, it, fn))
        print(f'  ✓ {fam} {w}{" kursiv" if it else ""}')

fams = {f[0] for f in faces}
for need in [x for x in (sf.get('text'), sf.get('akzent')) if x]:
    if need not in fams:
        print(f'⚠ Schrift „{need}“ nicht gefunden (vorhanden: {sorted(fams) or "keine"}). '
              f'Google-Fonts-Namen prüfen oder TTF/OTF-Dateien nach {FD} legen und erneut starten.')
if faces:
    css = ''.join(f"@font-face{{font-family:'{fam}';src:url('{fn}') format('{'opentype' if fn.endswith('.otf') else 'truetype'}');"
                  f"font-weight:{w};font-style:{'italic' if it else 'normal'};font-display:block;}}\n" for fam, w, it, fn in faces)
    open(os.path.join(FD, 'fonts.css'), 'w').write(css)
    text = [f for f in faces if f[0] == sf['text'] and not f[2]] or faces
    bold = min(text, key=lambda f: abs(f[1] - 600))
    json.dump(widths(os.path.join(FD, bold[3])), open(os.path.join(FD, 'breiten.json'), 'w'), ensure_ascii=False)
    print(f'  → fonts.css ({len(faces)} Schnitte), breiten.json aus {bold[0]} {bold[1]}')


# ───────── Kanalbild ─────────
if '--avatar-von-kanal' in args:
    url = P['kanal'].get('url')
    if not url:
        print('⚠ kanal.url fehlt – Kanalbild übersprungen')
    else:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'de-DE,de;q=0.9',
                                                   'Cookie': 'SOCS=CAI; CONSENT=YES+'})
        html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
        m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if not m:
            print('⚠ Kein og:image auf der Kanalseite gefunden – Kanalbild bitte als Datei ablegen')
        else:
            img = re.sub(r'=s\d+-', '=s900-', m.group(1))
            tmp = os.path.join(PR.PDIR, '_avatar_dl')
            download(img, tmp)
            dst = os.path.join(PR.PDIR, P['kanal'].get('avatar') or 'kanal-avatar.jpg')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-vf', 'scale=900:900:force_original_aspect_ratio=increase,crop=900:900',
                            '-q:v', '2', dst], check=True)
            os.remove(tmp)
            print(f'✓ Kanalbild → {dst}')


# ───────── Bild-Stile vorbelegen ─────────
b = raw.setdefault('bilder', {})
if not b.get('foto_stil'):
    b['foto_stil'] = (f"cinematic photograph, moody low-key lighting with {F['marke2']} ambient light from the left and a warm "
                      f"desk lamp glow from the right, shallow depth of field, premium editorial look, landscape 1536x1024. "
                      f"No text, no logos.")
json.dump(raw, open(PR.PFILE, 'w'), indent=1, ensure_ascii=False)

print('\nDateien im Profil:', ', '.join(sorted(os.listdir(PR.PDIR))))
print('Nächster Schritt: python3 $SK/scripts/vorschau.py  (Vorschaubild der Einblendungen in den eigenen Farben)')
