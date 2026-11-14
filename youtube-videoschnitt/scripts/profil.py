"""Profil des Kanals laden (Marke, Kanal, CTA, Ablage, Ton, Bilder) – Grundlage aller Skripte.

Das Profil liegt außerhalb des Skill-Ordners, damit es ein Update des Skills übersteht:
    ~/.config/youtube-videoschnitt/profil.json   (+ fonts/, icons/, Logo, Kanalbild)
Anderer Ort: Umgebungsvariable YTV_PROFIL=<ordner>.

Fehlende Felder werden aus profil-vorlage/profil.json ergänzt. Angelegt wird das Profil im
Einrichtungsinterview (references/einrichtung.md) und mit setup_profil.py fertiggestellt.

    python3 profil.py            # zeigt, ob ein Profil da ist und was noch fehlt
"""
import json, os, shutil, subprocess

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDIR = os.path.expanduser(os.environ.get('YTV_PROFIL') or '~/.config/youtube-videoschnitt')
PFILE = os.path.join(PDIR, 'profil.json')
VORLAGE = os.path.join(SKILL, 'profil-vorlage', 'profil.json')


def _strip(d):
    """Kommentarfelder ("_…") aus der Vorlage entfernen."""
    if isinstance(d, dict):
        return {k: _strip(v) for k, v in d.items() if not k.startswith('_')}
    if isinstance(d, list):
        return [_strip(x) for x in d]
    return d


def _merge(base, over):
    out = dict(base)
    for k, v in over.items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


DEFAULT = _strip(json.load(open(VORLAGE)))
EXISTS = os.path.exists(PFILE)
P = _merge(DEFAULT, _strip(json.load(open(PFILE)))) if EXISTS else DEFAULT


def get(path, default=None):
    """get('ton.musik') → Wert aus dem Profil."""
    cur = P
    for k in path.split('.'):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def pfile(name):
    """Datei aus dem Profilordner (Logo, Kanalbild …) – None, wenn nicht vorhanden."""
    if not name:
        return None
    p = os.path.join(PDIR, name)
    return p if os.path.exists(p) else None


def hex_rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return ','.join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def fonts_css():
    """@font-face-Regeln: eigene Schriften aus dem Profil, sonst die mitgelieferte Poppins."""
    own = os.path.join(PDIR, 'fonts', 'fonts.css')
    return open(own).read() if os.path.exists(own) else open(os.path.join(SKILL, 'assets/fonts/fonts.css')).read()


def font_files():
    d = os.path.join(PDIR, 'fonts')
    if os.path.exists(os.path.join(d, 'fonts.css')):
        return [os.path.join(d, f) for f in os.listdir(d) if f.endswith(('.woff2', '.woff', '.ttf', '.otf'))]
    d = os.path.join(SKILL, 'assets/fonts')
    return [os.path.join(d, f) for f in os.listdir(d) if f.endswith('.woff2')]


def glyph_widths():
    """Glyphenbreiten (em) der Textschrift im fetten Schnitt – für das Laufband hinter der Person."""
    own = os.path.join(PDIR, 'fonts', 'breiten.json')
    return json.load(open(own if os.path.exists(own) else os.path.join(SKILL, 'assets/fonts/poppins600_widths.json')))


def asset_files():
    """Alles, was build.py in jedes Segment verlinkt: GSAP, Schriften, Logo, Kanalbild, Icons."""
    files = [os.path.join(SKILL, 'assets/gsap.min.js')] + font_files()
    for key in ('marke.logo_hell', 'marke.logo_dunkel', 'kanal.avatar'):
        f = pfile(get(key))
        if f:
            files.append(f)
    icons = os.path.join(PDIR, 'icons')
    if os.path.isdir(icons):
        files += [os.path.join(icons, f) for f in os.listdir(icons) if f.endswith(('.png', '.jpg', '.webp', '.svg'))]
    return files


_ENC = None


def h264(bitrate='70M', maxrate=None):
    """Hardware-Encoder auf dem Mac (h264_videotoolbox), sonst libx264 in hoher Qualität."""
    global _ENC
    if _ENC is None:
        r = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], capture_output=True, text=True).stdout
        _ENC = 'h264_videotoolbox' if 'h264_videotoolbox' in r else 'libx264'
    if _ENC == 'h264_videotoolbox':
        return ['-c:v', 'h264_videotoolbox', '-b:v', bitrate] + (['-maxrate', maxrate] if maxrate else [])
    return ['-c:v', 'libx264', '-crf', '12', '-preset', 'fast']


def font_file(weight=500):
    """TTF/OTF der Textschrift in der gewünschten Stärke (für Bilder, die ohne Browser entstehen, z. B. das
    Werbung-Label). Eigene Schriften aus dem Profil, sonst die mitgelieferte Poppins (wird einmalig nach TTF gewandelt)."""
    d = os.path.join(PDIR, 'fonts')
    fam = (get('marke.schriften.text') or 'Poppins').replace(' ', '')
    if os.path.isdir(d):
        cands = [f for f in os.listdir(d) if f.lower().endswith(('.ttf', '.otf')) and fam.lower() in f.lower().replace(' ', '')]
        hit = [f for f in cands if f'-{weight}' in f and 'italic' not in f.lower()] or cands
        if hit:
            return os.path.join(d, sorted(hit)[0])
    ttf = os.path.expanduser(f'~/.cache/youtube-videoschnitt/Poppins-{weight}.ttf')
    if not os.path.exists(ttf):
        from fontTools.ttLib import TTFont
        os.makedirs(os.path.dirname(ttf), exist_ok=True)
        f = TTFont(os.path.join(SKILL, f'assets/fonts/Poppins-{weight}-normal.woff2'))
        f.flavor = None
        f.save(ttf)
    return ttf


def partner_dir(name):
    """Ordner eines Werbepartners (partner.json + Logos): <Profil>/partner/<name>, sonst None."""
    for d in (os.path.join(PDIR, 'partner', name), os.path.join(SKILL, 'assets', 'partner', name)):
        if os.path.isfile(os.path.join(d, 'partner.json')):
            return d
    return None


def codex_path():
    p = get('bilder.codex_pfad') or '/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex'
    if os.path.exists(p):
        return p
    return shutil.which('codex')


if __name__ == '__main__':
    if not EXISTS:
        print(f'✗ Kein Profil unter {PFILE} – erst das Einrichtungsinterview führen (references/einrichtung.md).')
        raise SystemExit(1)
    print(f'✓ Profil: {PFILE}')
    miss = []
    if not get('kanal.name'):
        miss.append('kanal.name')
    if get('cta.aktiv') and not get('cta.url'):
        miss.append('cta.url')
    if not pfile(get('kanal.avatar')):
        miss.append('Kanalbild (kanal.avatar) – Abo-Störer zeigt sonst Initialen')
    if not pfile(get('marke.logo_hell')):
        miss.append('Logo (marke.logo_hell) – Endkarte zeigt sonst nur Text')
    if not os.path.exists(os.path.join(PDIR, 'fonts', 'fonts.css')):
        miss.append('eigene Schrift (setup_profil.py) – es gilt die mitgelieferte Poppins')
    print('Offen:' if miss else 'Alles da.', *('\n  • ' + m for m in miss))
