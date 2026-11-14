"""Schritt 4: geschnittenes 4K-Basisvideo (ohne Ton) aus der Schnittliste rendern.

Die Quelle wird blockweise mit select-Filtern gerendert (eine einzige Filterzeile mit hunderten
Bereichen sprengt ffmpeg) und danach verlustfrei aneinandergehängt. Hardware-Encoder (Mac) oder x264, dichte GOP
(-g 30), damit HyperFrames später jeden Frame sauber anspringen kann. Quelle < 4K wird auf 3840×2160 skaliert.
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profil as PR
from concurrent.futures import ThreadPoolExecutor

CFG = json.load(open('project.json'))
FPS = CFG.get('fps', 30)
src = CFG['source']
edl = json.load(open('edl.json'))
os.makedirs('chunks', exist_ok=True)
C = 30
jobs = []
for ci in range(0, len(edl), C):
    seg = edl[ci:ci + C]
    f0, f1 = round(seg[0][0] * FPS), round(seg[-1][1] * FPS)
    terms = '+'.join(f"between(n\\,{round(s*FPS)-f0}\\,{round(e*FPS)-1-f0})" for s, e, _ in seg)
    fn = f'chunks/sel_{ci//C:02d}.txt'
    open(fn, 'w').write(f"select='{terms}',setpts=N/({FPS}*TB),scale=3840:2160:flags=lanczos")
    out = f'chunks/c_{ci//C:02d}.mp4'
    jobs.append((['ffmpeg', '-v', 'error', '-y', '-ss', f'{(f0 - 0.5)/FPS:.6f}', '-t', f'{(f1-f0)/FPS+0.5:.4f}', '-i', src, '-an',
                  '-/filter:v', fn, *PR.h264('70M', '90M'), '-g', '30',
                  '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', out], out))


def go(j):
    if not os.path.exists(j[1]):
        subprocess.run(j[0], check=True)
    print('fertig', j[1], flush=True)


with ThreadPoolExecutor(3) as ex:
    list(ex.map(go, jobs))

# ── Vollbild-Kamera-Einschübe: Bild aus der „Kamera only“-Datei, Ton bleibt aus dem Hauptvideo ──
cam = CFG.get('camera') or {}
cuts = CFG.get('camera_cuts', [])
# Optional: eigener Versatz je Einschub (die Aufnahmesoftware verliert gelegentlich Frames → Versatz springt, siehe pitfalls)
COFF = CFG.get('camera_cut_offsets') or []
final = [o for _, o in jobs]
if cuts and cam.get('file'):
    off = cam['offset']                     # Kamerazeit = Hauptzeit + offset (sync_cam.py)
    # Bildausschnitt wie die Vollbild-Kamera-Szene im Hauptvideo (match_crop.py) – sonst aus dem Profil, sonst ungeschnitten
    cr = cam.get('crop') or PR.get('aufnahme.kamera_spur.crop')
    cropf = f"crop={cr['w']}:{cr['h']}:{cr['x']}:{cr['y']}," if cr else ''
    if not cr:
        print('⚠ Kein camera.crop – Kamera-Einschübe werden ungeschnitten eingesetzt. Besser vorher match_crop.py laufen lassen.')
    for ci in range(0, len(edl), C):
        seg = edl[ci:ci + C]
        local, pieces = 0, []
        for s, e, _ in seg:
            for k, (a, b) in enumerate(cuts):
                co = COFF[k] if k < len(COFF) else off
                ps, pe = max(s, a), min(e, b)
                if pe - ps >= 2 / FPS:
                    f0 = round((local + ps - s) * FPS)
                    nf = round((pe - ps) * FPS)
                    pieces.append((f0, nf, round((ps + co) * FPS) / FPS))
            local += (round(e * FPS) - round(s * FPS)) / FPS
        if not pieces:
            continue
        src_chunk = f'chunks/c_{ci//C:02d}.mp4'
        out = f'chunks/c_{ci//C:02d}_cam.mp4'
        if not os.path.exists(out):
            ins, fc, prev = ['-i', src_chunk], [], '[0:v]'
            for k, (f0, nf, ct) in enumerate(pieces, start=1):
                ins += ['-ss', f'{ct - 0.5/FPS:.6f}', '-t', f'{nf/FPS + 0.2:.4f}', '-i', cam['file']]
                fc.append(f'[{k}:v]trim=end_frame={nf},setpts=PTS-STARTPTS+{f0}/({FPS}*TB),{cropf}scale=3840:2160:flags=lanczos[k{k}]')
                fc.append(f'{prev}[k{k}]overlay=eof_action=pass:repeatlast=0[v{k}]')
                prev = f'[v{k}]'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', ';'.join(fc), '-map', prev, '-an',
                            *PR.h264('70M', '90M'), '-g', '30', '-pix_fmt', 'yuv420p',
                            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', out], check=True)
        final[ci // C] = out
        print(f'Kamera-Einschübe in Block {ci//C}: {len(pieces)}', flush=True)
open('chunks/list.txt', 'w').write(''.join(f"file '{os.path.abspath(o)}'\n" for o in final))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'chunks/list.txt', '-c', 'copy',
                '-movflags', '+faststart', 'base.mp4'], check=True)
n = int(subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v:0', '-show_entries',
                        'stream=nb_read_packets', '-of', 'csv=p=0', 'base.mp4'], capture_output=True, text=True).stdout)
exp = sum(round(e * FPS) - round(s * FPS) for s, e, _ in edl)
print(f'base.mp4: {n} Frames (erwartet {exp})', 'OK' if abs(n - exp) <= 2 else '⚠ ABWEICHUNG')
