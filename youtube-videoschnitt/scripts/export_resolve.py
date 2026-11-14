"""Optional: den Schnitt als DaVinci-Resolve-Timeline exportieren, zum Nachjustieren von Hand.

Im Arbeitsordner ausführen, nachdem render_base.py, render_all.sh und mix.py gelaufen sind:
    python3 <skill>/scripts/export_resolve.py
Ergebnis: <Arbeitsordner>/resolve/<Videotitel>.xml (Final-Cut-7-XML), dazu in resolve/ der Originalton und die Soundeffekte als WAV.
In Resolve: Datei → Importieren → Timeline (geht auch in der Gratisversion).

Warum FCP7-XML und nicht FCPXML: FCPXML kennt keine festen Tonspuren, Resolve verteilt verbundene Clips
dann wild auf A1/A2. FCP7-XML legt jede Spur ausdrücklich fest.

Spuren in Resolve:
  V1  Schnitt aus der Quelle (project.json „source“ + edl.json), Originalton verlinkt auf A1.
      Jeder Clip hat das weggeschnittene Material als Reserve, Schnitte lassen sich frei verschieben.
  V2  Kamera-Einschübe (camera_cuts) mit demselben Bildausschnitt wie render_base.py
  V3  fertige Grafik-Blöcke aus renders/. Deckend, Grafik und Push-ins sind eingebacken.
      Zum Arbeiten am Schnitt die Spur ausschalten, sonst sieht man V1/V2 nicht.
  A1  Originalton zu V1 (als WAV in resolve/, mit V1 verlinkt)
  A2  Musik (stem_music.wav, schon geduckt)
  A3… Soundeffekte einzeln aus manifest.json, Lautstärke wie in mix.py
  zuletzt Stimme gemastert (stem_voice.wav), ausgeschaltet, nur als Referenz
Kapitelmarken aus ../<profil.ablage.kapitel_datei> kommen als Timeline-Marker.
"""
import json, math, os, re, subprocess, wave
from urllib.parse import quote
from xml.sax.saxutils import escape
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profil as PR

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open('project.json'))
FPS = CFG.get('fps', 30)
SR = 48000
W, H = 3840, 2160
edl = json.load(open('edl.json'))
manifest = json.load(open('manifest.json')) if os.path.exists('manifest.json') else []
video_dir = os.path.dirname(os.getcwd())
title = re.sub(r'^\d{4}-\d{2}-\d{2}\s+', '', os.path.basename(video_dir))
os.makedirs('resolve/sfx', exist_ok=True)
RATE = f'<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>'


def probe(path, entries):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', entries, '-of', 'json', path],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def vframes(path):
    s = probe(path, 'stream=codec_type,nb_frames:format=duration')
    v = [x for x in s['streams'] if x['codec_type'] == 'video']
    if v and v[0].get('nb_frames'):
        return int(v[0]['nb_frames'])
    return round(float(s['format']['duration']) * FPS)


def has_audio(path):
    return any(x['codec_type'] == 'audio' for x in probe(path, 'stream=codec_type')['streams'])


def samples(path):
    s = probe(path, 'stream=codec_type,duration_ts,sample_rate:format=duration')
    a = [x for x in s['streams'] if x['codec_type'] == 'audio'][0]
    return round(float(s['format']['duration']) * int(a['sample_rate']))


def write_wav(path, x):
    o = wave.open(path, 'wb'); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
    o.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); o.close()


def decode(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


# ── Dateien ──
files = {}


def register(path, video, audio, frames):
    if path not in files:
        files[path] = {'id': f'file-{len(files) + 1}', 'video': video, 'audio': audio, 'frames': frames}
    return path


def file_ref(path):
    return f'<file id="{files[path]["id"]}"/>'


def file_def(path):
    """Volle Dateibeschreibung. Kommt beim Schreiben an die erste Fundstelle im Dokument, sonst findet Resolve die Datei nicht."""
    f = files[path]
    media = ''
    if f['video']:
        media += (f'<video><samplecharacteristics>{RATE}<width>{W}</width><height>{H}</height>'
                  '<pixelaspectratio>square</pixelaspectratio></samplecharacteristics></video>')
    if f['audio']:
        media += f'<audio><samplecharacteristics><depth>16</depth><samplerate>{SR}</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>'
    return (f'<file id="{f["id"]}"><name>{escape(os.path.basename(path))}</name>'
            f'<pathurl>file://localhost{quote(os.path.abspath(path))}</pathurl>{RATE}'
            f'<duration>{f["frames"]}</duration><media>{media}</media></file>')


def clip(cid, name, path, start, dur, src_in, kind, enabled=True, extra='', links=''):
    f = files[path]
    st = f'<sourcetrack><mediatype>{kind}</mediatype><trackindex>1</trackindex></sourcetrack>' if kind == 'audio' else ''
    return (f'<clipitem id="{cid}"><name>{escape(name)}</name><enabled>{"TRUE" if enabled else "FALSE"}</enabled>'
            f'<duration>{f["frames"]}</duration>{RATE}<start>{start}</start><end>{start + dur}</end>'
            f'<in>{src_in}</in><out>{src_in + dur}</out>{file_ref(path)}{st}{extra}{links}</clipitem>')


def level(db):
    return ('<filter><effect><name>Audio Levels</name><effectid>audiolevels</effectid><effectcategory>audiolevels</effectcategory>'
            '<effecttype>audiolevels</effecttype><mediatype>audio</mediatype><parameter><parameterid>level</parameterid>'
            f'<name>Level</name><valuemin>0</valuemin><valuemax>3.98109</valuemax><value>{10 ** (db / 20):.5f}</value>'
            '</parameter></effect></filter>')


# ── V1 + A1: Schnitt aus der Quelle ──
src = CFG['source']
register(src, True, False, vframes(src))
# Originalton als eigene WAV: Ton aus MP4 ordnet Resolve beim FCP7-XML nicht zu („File not found“), WAV klappt.
src_audio = None
if has_audio(src):
    src_audio = os.path.join('resolve', os.path.splitext(os.path.basename(src))[0] + '_ton.wav')
    if not os.path.exists(src_audio):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '2', '-ar', str(SR), '-c:a', 'pcm_s16le', src_audio], check=True)
    register(src_audio, False, True, samples(src_audio) * FPS // SR)
spine, T = [], 0
for s, e, kind in edl:
    f0, f1 = round(s * FPS), round(e * FPS)
    if f1 > f0:
        spine.append((T, f0, f1 - f0, kind, s, e))
        T += f1 - f0
TOTAL = T
v1, a1 = [], []
for i, (T0, f0, d, kind, _, _) in enumerate(spine, 1):
    name = f"{'Talking Head' if kind == 'TH' else 'Bildschirm'} {i:03d}"
    links = ''
    if src_audio:
        links = (f'<link><linkclipref>v1-{i}</linkclipref><mediatype>video</mediatype><trackindex>1</trackindex><clipindex>{i}</clipindex></link>'
                 f'<link><linkclipref>a1-{i}</linkclipref><mediatype>audio</mediatype><trackindex>1</trackindex><clipindex>{i}</clipindex><groupindex>1</groupindex></link>')
        a1.append(clip(f'a1-{i}', name, src_audio, T0, d, f0, 'audio', links=links))
    v1.append(clip(f'v1-{i}', name, src, T0, d, f0, 'video', links=links))

# ── V2: Kamera-Einschübe (wie render_base.py) ──
cam, cuts = CFG.get('camera') or {}, CFG.get('camera_cuts', [])
COFF = CFG.get('camera_cut_offsets') or []
v2 = []
if cam.get('file') and cuts:
    register(cam['file'], True, False, vframes(cam['file']))
    cr = cam.get('crop') or {'x': 356, 'y': 0, 'w': 3164, 'h': 1780}
    sc = W / cr['w']
    # Basic Motion: Mittelpunkt als Anteil der Bildgröße, (0,0) = Bildmitte, y nach unten
    cx = -sc * (cr['x'] + cr['w'] / 2 - W / 2) / W
    cy = -sc * (cr['y'] + cr['h'] / 2 - H / 2) / H
    motion = ('<filter><effect><name>Basic Motion</name><effectid>basic</effectid><effectcategory>motion</effectcategory>'
              '<effecttype>motion</effecttype><mediatype>video</mediatype>'
              f'<parameter><parameterid>scale</parameterid><name>Scale</name><valuemin>0</valuemin><valuemax>1000</valuemax><value>{sc * 100:.3f}</value></parameter>'
              f'<parameter><parameterid>center</parameterid><name>Center</name><value><horiz>{cx:.5f}</horiz><vert>{cy:.5f}</vert></value></parameter>'
              '</effect></filter>')
    for T0, _, _, _, s, e in spine:
        for k, (a, b) in enumerate(cuts):
            co = COFF[k] if k < len(COFF) else cam['offset']
            ps, pe = max(s, a), min(e, b)
            if pe - ps >= 2 / FPS:
                v2.append(clip(f'v2-{len(v2) + 1}', 'Kamera', cam['file'], T0 + round((ps - s) * FPS),
                               round((pe - ps) * FPS), round((ps + co) * FPS), 'video', extra=motion))

# ── V3: fertige Grafik-Blöcke ──
v3, blocks = [], []
for m in manifest:
    p = f"renders/{m['id']}.mp4"
    if os.path.exists(p):
        blocks.append((round(m['t0'] * FPS), m['id'], p))
    else:
        print('⚠ fehlt:', p)
for j, (T0, mid, p) in enumerate(blocks):
    nf = vframes(p)
    register(p, True, False, nf)
    end = blocks[j + 1][0] if j + 1 < len(blocks) else TOTAL
    v3.append(clip(f'v3-{j + 1}', f'Grafik {mid}', p, T0, min(nf, end - T0), 0, 'video'))

# ── A2: Musik ──
a2 = []
if os.path.exists('stem_music.wav'):
    n = samples('stem_music.wav')
    register('stem_music.wav', False, True, n * FPS // SR)
    a2.append(clip('a2-1', 'Musik', 'stem_music.wav', 0, min(n * FPS // SR, TOTAL), 0, 'audio'))

# ── A3…: Soundeffekte (als WAV, mindestens 0,1 s, damit Resolve auch die 60-ms-Ticks annimmt) ──
sfx, cache = [], {}
for m in manifest:
    for t, name, g in m.get('sfx', []):
        if name not in cache:
            x = decode(os.path.join(SKILL, 'assets/sfx', f'{name}.mp3'))
            peak = float(np.abs(x).max()) + 1e-9
            pad = max(len(x), SR // 10)
            x = np.vstack([x, np.zeros((pad - len(x), 2), np.float32)])
            p = f'resolve/sfx/{name}.wav'
            write_wav(p, x)
            register(p, False, True, len(x) * FPS // SR)
            cache[name] = (p, len(x) * FPS // SR, peak)
        p, nfr, peak = cache[name]
        T0 = round(max(0.0, t - (0.12 if name.startswith('whoosh') else 0)) * FPS)
        d = min(nfr, TOTAL - T0)
        if d > 0:
            sfx.append((T0, d, name, 20 * math.log10(g * 1.6 * 10 ** (-12 / 20) / peak), p))
sfx.sort()
lanes, ends = [], []
for T0, d, name, gain, p in sfx:
    li = next((i for i, en in enumerate(ends) if en <= T0), None)
    if li is None:
        lanes.append([]); ends.append(0); li = len(lanes) - 1
    ends[li] = T0 + d
    lanes[li].append(clip(f'sfx{li}-{len(lanes[li]) + 1}', name, p, T0, d, 0, 'audio', extra=level(gain)))

# ── Stimme gemastert als Referenz ──
aref = []
if os.path.exists('stem_voice.wav'):
    n = samples('stem_voice.wav')
    register('stem_voice.wav', False, True, n * FPS // SR)
    aref.append(clip('aref-1', 'Stimme gemastert (Referenz)', 'stem_voice.wav', 0, min(n * FPS // SR, TOTAL), 0, 'audio', enabled=False))

# ── Kapitelmarken ──
marks = []
chap = os.path.join(video_dir, PR.get('ablage.kapitel_datei') or 'Kapitelmarken.txt')
if os.path.exists(chap):
    for line in open(chap, encoding='utf-8'):
        mm = re.match(r'\s*(\d+):(\d{2})(?::(\d{2}))?\s+(.+)', line)
        if mm:
            a, b, c3, txt = mm.groups()
            sec = int(a) * 3600 + int(b) * 60 + int(c3) if c3 else int(a) * 60 + int(b)
            marks.append(f'<marker><name>{escape(txt.strip())}</name><comment/><in>{min(sec * FPS, TOTAL - 1)}</in><out>-1</out></marker>')


def track(items):
    return '<track>' + ''.join(items) + '<enabled>TRUE</enabled><locked>FALSE</locked></track>'


audio_tracks = [a1, a2] + lanes + [aref]
xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="5">\n'
       f'<sequence id="sequence-1"><name>{escape(title)}</name><duration>{TOTAL}</duration>{RATE}'
       f'<timecode>{RATE}<string>00:00:00:00</string><frame>0</frame><displayformat>NDF</displayformat></timecode>'
       '<media><video><format><samplecharacteristics>'
       f'{RATE}<width>{W}</width><height>{H}</height><pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>\n'
       + '\n'.join(track(t) for t in (v1, v2, v3)) +
       '\n</video><audio><numOutputChannels>2</numOutputChannels>\n'
       + '\n'.join(track(t) for t in audio_tracks if t) +
       '\n</audio></media>' + ''.join(marks) + '</sequence>\n</xmeml>\n')
for path in files:
    ref = file_ref(path)
    i = xml.find(ref)
    if i >= 0:
        xml = xml[:i] + file_def(path) + xml[i + len(ref):]
out = os.path.join('resolve', f'{title}.xml')
open(out, 'w', encoding='utf-8').write(xml)
old = os.path.join('resolve', f'{title}.fcpxml')
if os.path.exists(old):
    os.remove(old)
print(f'{out}: V1 {len(v1)} Schnitte, V2 {len(v2)} Kamera-Einschübe, V3 {len(v3)} Grafik-Blöcke, '
      f'{len(sfx)} Soundeffekte auf {len(lanes)} Spuren, {len(marks)} Kapitelmarken, '
      f'Länge {TOTAL} Frames ({TOTAL / FPS:.2f}s)')
