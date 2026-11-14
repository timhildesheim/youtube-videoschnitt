"""Schritt 11: finales 4K-Video – Basis + gerenderte Segmente + Endkarte + Mix (Ziel-Lautheit aus dem Profil, Standard −14 LUFS).

    python3 assemble.py "<Ausgabedatei.mp4>"

Video: Segmente werden per Overlay-Kette zeitgenau über base.mp4 gelegt (sie sind vollflächig und
ersetzen das Bild), Endkarte angehängt, x264 CRF 16 (Bildschirmaufnahmen landen dabei bei ~13 Mbit/s –
das ist inhaltsbedingt, nicht zu wenig). Ton: nur Pegel auf Ziel-LUFS + Spitzenbegrenzer, Klang unverändert.
"""
import json, os, re, subprocess, sys

W = os.getcwd()
OUT = os.path.abspath(sys.argv[1])
man = json.load(open('manifest.json'))
CFG = json.load(open('project.json'))
FPS = CFG.get('fps', 30)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profil as PR
TARGET = float(PR.get('ton.ziel_lufs', -14))

# Lautheit: NUR Pegel anheben auf Ziel-LUFS + Spitzenbegrenzer bei -1,5 dBFS. Kein Kompressor, kein dynamisches
# loudnorm – die Stimme soll klingen wie aufgenommen.
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', 'mix_pre.wav', '-af', 'ebur128=framelog=quiet', '-f', 'null', '-'],
                   capture_output=True, text=True)
I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r.stderr)[-1])
gain = TARGET - I
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'mix_pre.wav', '-af',
                f'volume={gain:.2f}dB,alimiter=limit=0.84:attack=1:release=60:level=false,aresample=48000',
                '-c:a', 'pcm_s24le', 'mix_final.wav'], check=True)
st = {'input_i': I}
print('Ton normalisiert:', st['input_i'], f'LUFS → {TARGET}')

segs = [m for m in man if m['kind'] != 'end']
ends = [m for m in man if m['kind'] == 'end']
inputs = ['-i', 'base.mp4'] + sum([['-i', f'renders/{m["id"]}.mp4'] for m in segs + ends], []) + ['-i', 'mix_final.wav']
fc, prev = [], '[0:v]'
for k, m in enumerate(segs, start=1):
    fc.append(f'[{k}:v]setpts=PTS-STARTPTS+{m["t0"]:.4f}/TB[o{k}]')
    fc.append(f'{prev}[o{k}]overlay=eof_action=pass:repeatlast=0[v{k}]')
    prev = f'[v{k}]'
ke = len(segs) + 1
if ends:
    fc.append(f'{prev}settb=1/{FPS},setpts=N/{FPS}/TB[main];[{ke}:v]settb=1/{FPS},setpts=N/{FPS}/TB[endv];[main][endv]concat=n=2:v=1:a=0,format=yuv420p[vout]')
    ai = ke + 1
else:
    fc.append(f'{prev}format=yuv420p[vout]')
    ai = ke

# Werbekennzeichnung (bezahlte Kooperation): das Wort „Werbung“ (profil.texte.werbung) oben rechts, dezent in marke3
# mit 30 % Deckkraft, Textschrift 500, 4K: 54 px, 48 px vom rechten und 40 px vom oberen Rand.
# Aktiv, wenn project.json "sponsor" hat (abschalten mit "ad_label": false) oder "ad_label": true / "Anzeige".
# Ob 30 % Deckkraft im eigenen Land als „gut lesbar“ gilt, selbst prüfen (in Deutschland: Landesmedienanstalten).
ad = CFG.get('ad_label', bool(CFG.get('sponsor')))
if ad:
    from PIL import Image, ImageDraw, ImageFont   # in der Python-Umgebung aus check_env.sh enthalten
    ttf = PR.font_file(500)
    txt = ad if isinstance(ad, str) else (PR.get('texte.werbung') or 'Werbung')
    font = ImageFont.truetype(ttf, 54)
    l, t, r, btm = font.getbbox(txt)
    im = Image.new('RGBA', (r + 8, btm + 8), (0, 0, 0, 0))
    col = tuple(int(x) for x in PR.hex_rgb(PR.get('marke.farben.marke3')).split(','))
    ImageDraw.Draw(im).text((0, 0), txt, font=font, fill=col + (round(255 * 0.30),))
    im.save('ad_label.png')
    inputs += ['-loop', '1', '-i', 'ad_label.png']
    fc[-1] = fc[-1].replace('[vout]', '[vpre]')
    # Nur in bestimmten Abschnitten: "ad_label_ranges": [[von, bis], …] in QUELLZEIT wie im Storyboard
    # (nur dort, wo über den Partner gesprochen wird). Ohne Angabe läuft das Label durchgehend.
    rng = CFG.get('ad_label_ranges')
    en = ''
    if rng:
        from lib import S
        win = [(S(x), S(y) if y != 'end' else 1e9) for x, y in rng]
        en = ":enable='" + '+'.join(f'between(t,{x:.3f},{y:.3f})' for x, y in win) + "'"
        print('Werbekennzeichnung nur in:', ', '.join(f'{int(x//60)}:{x%60:05.2f}–{int(y//60)}:{y%60:05.2f}' for x, y in win))
    fc.append(f'[vpre][{ai + 1}:v]overlay=x=W-{48 + r}:y={40 - t}:shortest=1{en},format=yuv420p[vout]')
    print('Werbekennzeichnung:', txt)
open('assemble_filter.txt', 'w').write(';\n'.join(fc))
subprocess.run(['ffmpeg', '-hide_banner', '-v', 'error', '-stats', '-y', *inputs, '-/filter_complex', 'assemble_filter.txt',
                '-map', '[vout]', '-map', f'{ai}:a', '-c:v', 'libx264', '-preset', 'fast', '-crf', '16', '-profile:v', 'high',
                '-g', '60', '-bf', '2', '-x264-params', 'aq-mode=3', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                '-colorspace', 'bt709', '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-shortest', '-movflags', '+faststart', OUT], check=True)
p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height,bit_rate', '-show_entries', 'format=duration',
                    '-of', 'compact', OUT], capture_output=True, text=True).stdout
print('FERTIG', OUT, '\n', p)
