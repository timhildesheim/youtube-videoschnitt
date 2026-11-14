"""Schritt 7: aus story.py je Segment ein HyperFrames-Projekt bauen.

    python3 build.py            # alle Segmente
    python3 build.py s03 th1    # nur diese

Pro Segment (segs/<id>/): index.html, bg.mp4 (Ausschnitt aus base.mp4, dichte GOP), Freistellungen
cut_<id>.webm für Text-hinter-Person, Symlinks auf Schriften/Icons/Logo/Kanalbild (Profil) und GSAP. Schreibt manifest.json.
Vorhandene bg.mp4/cut_*.webm werden wiederverwendet – index.html wird immer neu geschrieben.
"""
import importlib.util, json, os, subprocess, sys

W = os.getcwd()
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ['YT_WORK'] = W
sys.path.insert(0, os.path.join(SKILL, 'scripts'))
import profil as PR
spec = importlib.util.spec_from_file_location('story', os.path.join(W, 'story.py'))
story = importlib.util.module_from_spec(spec)
spec.loader.exec_module(story)
comps = story.comps
only = set(sys.argv[1:])
BASE = os.path.join(W, 'base.mp4')
ASSETS = PR.asset_files()
_sp = json.load(open(os.path.join(W, 'project.json'))).get('sponsor')   # Werbepartner-Logos (<Profil>/partner/<name>)
if _sp:
    _pd = PR.partner_dir(_sp if isinstance(_sp, str) else _sp['partner'])
    if _pd:
        ASSETS += [os.path.join(_pd, f) for f in os.listdir(_pd) if f.endswith(('.png', '.jpg', '.svg', '.webp'))]
EXTRA = os.path.join(W, 'assets')  # projektspezifische Bilder (Screenshots, Codex-Grafiken)
if os.path.isdir(EXTRA):
    ASSETS += [os.path.join(EXTRA, f) for f in os.listdir(EXTRA) if not f.startswith('.')]

ids = [c.id for c in comps]
dups = {i for i in ids if ids.count(i) > 1}
assert not dups, f'Doppelte Segment-IDs: {dups}'


def run(cmd):
    subprocess.run(cmd, check=True)


manifest = []
for c in comps:
    manifest.append({'id': c.id, 't0': c.t0, 't1': c.t1, 'dur': c.dur, 'kind': c.kind, 'sfx': c.sfx, 'cues': getattr(c, 'cues', [])})
    if only and c.id not in only:
        continue
    d = os.path.join(W, 'segs', c.id)
    os.makedirs(d, exist_ok=True)
    for a in ASSETS:   # spätere Einträge (Projekt-Assets) gewinnen bei gleichem Namen
        dst = os.path.join(d, os.path.basename(a))
        if os.path.islink(dst) and os.readlink(dst) != a:
            os.remove(dst)
        if not os.path.lexists(dst):
            os.symlink(a, dst)
    open(os.path.join(d, 'index.html'), 'w').write(c.html())
    bg = os.path.join(d, 'bg.mp4')
    # Wiederverwenden nur, wenn der Ausschnitt noch zu Start und Länge des Segments passt (bg.key). Sonst zeigt das
    # Segment altes Bild: verschobener Start → Mund nicht lippensynchron, kürzer → Standbild.
    key = f'{round(c.t0 * 30)} {round(c.dur * 30)} {int(os.path.getmtime(BASE))}' if c.kind != 'end' else f'end {round(c.dur * 30)}'
    kf = os.path.join(d, 'bg.key')
    if os.path.exists(bg):
        old = open(kf).read().strip() if os.path.exists(kf) else None
        if old is None:   # alte Segmente ohne Schlüssel: wenigstens die Länge prüfen
            dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', bg],
                                       capture_output=True, text=True).stdout or 0)
            stale = abs(dur - c.dur) > 0.05
        else:
            stale = old != key
        if stale:
            print(f'{c.id}: bg.mp4 passt nicht mehr zum Segment → neu', flush=True)
            for f in os.listdir(d):
                if f == 'bg.mp4' or f.startswith('cut_') or f.startswith('snip_'):
                    os.remove(os.path.join(d, f))
    if not os.path.exists(bg):
        if c.kind == 'end':   # Endkarte: letztes Bild einfrieren
            run(['ffmpeg', '-v', 'error', '-y', '-sseof', '-0.1', '-i', BASE, '-frames:v', '1', f'{d}/last.png'])
            run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', f'{d}/last.png', '-t', f'{c.dur:.4f}', '-r', '30',
                 *PR.h264('40M'), '-g', '15', '-pix_fmt', 'yuv420p', bg])
        else:
            # framegenau: halbes Frame vor dem Ziel seeken + feste Frame-Zahl (mit '-ss t0:.4f' landete der Ausschnitt
            # je nach Rundung 1 Frame zu spät → Bild 33 ms vor dem Ton)
            f0, nf = round(c.t0 * 30), round(c.dur * 30)
            run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{(f0 - 0.5) / 30:.6f}', '-i', BASE, '-frames:v', str(nf), '-an',
                 *PR.h264('80M'), '-g', '15', '-pix_fmt', 'yuv420p',
                 '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', bg])
        open(kf, 'w').write(key)
    elif not os.path.exists(kf):
        open(kf, 'w').write(key)
    for cid, a, b in c.cutouts:
        out = os.path.join(d, f'cut_{cid}.webm')
        if os.path.exists(out):
            continue
        snip = os.path.join(d, f'snip_{cid}.mp4')
        run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{(round(a * 30) - 0.5) / 30:.6f}', '-i', bg, '-frames:v', str(round((b - a) * 30)), '-an',
             '-c:v', 'libx264', '-crf', '10', '-preset', 'fast', '-g', '15', '-pix_fmt', 'yuv420p', snip])
        subprocess.run(['npx', 'hyperframes', 'remove-background', snip, '-o', out, '--quality', 'best'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('gebaut', c.id, f'{c.dur:.1f}s', flush=True)

json.dump(manifest, open(os.path.join(W, 'manifest.json'), 'w'), indent=1)
print(f'{len(comps)} Segmente, zusammen {sum(c.dur for c in comps)/60:.1f} min → manifest.json')
