#!/bin/bash
# Schritt 8: alle Segmente in 4K rendern (3 Spuren parallel), fertige überspringen, Fehlschläge einmal nachholen.
# Im Arbeitsordner aufrufen. Lock verhindert, dass zwei Läufe dieselben Dateien beschreiben
# (ist in der ersten Produktion passiert: zwei Warteschlangen → Kollisionen beim Verschieben).
#
# Parallelität (gemessen Nov. 2026 auf einem M4 Max, 16 Kerne / 64 GB, 8 Segmente mit zusammen 112 s):
# HyperFrames hat eine eigene Render-Sperre (ein Render pro Benutzerkonto, ~/.cache/hyperframes/locks).
# Das frühere „2 parallel“ lief deshalb faktisch nacheinander: 168 s. Mit HYPERFRAMES_RENDER_LOCK=off:
# 2 Spuren × 5 Worker 147 s, 3 Spuren × 4 Worker 135 s (−20 %), 4 Spuren × 3 Worker ebenfalls 135 s bei
# deutlich höherer Last. RAM in allen Fällen ~23 GB für Chrome/ffmpeg/Node, mindestens 28 % frei.
# ffmpeg bekommt von HyperFrames immer -threads = alle Kerne, das lässt sich nicht begrenzen. Darum laufen die
# Renders mit nice 10: deine Apps haben Vorrang, der Rechner bleibt bedienbar.
# Weniger Kerne oder RAM (z. B. 16 GB): RENDER_LANES=1 RENDER_WORKERS=4 bash render_all.sh
# Mehr Ruhe beim Nebenherarbeiten: RENDER_LANES=2 bash render_all.sh (oder 1).
W=$(pwd)
LOCK="$W/.render.lock"
if ! mkdir "$LOCK" 2>/dev/null; then echo "Render läuft schon (Lock $LOCK). Abbruch."; exit 1; fi
trap 'rmdir "$LOCK"' EXIT
mkdir -p "$W/renders"
export NODE_OPTIONS=--max-old-space-size=8192
export HYPERFRAMES_RENDER_LOCK=off

LANES=${RENDER_LANES:-3}
WORKERS=${RENDER_WORKERS:-4}
# Plattenplatz: jede Spur legt die Einzelbilder ab (~16 GB pro 2 min 4K), parallel addiert sich das.
FREE_GB=$(df -Pk "$W" | awk 'NR==2 {print int($4/1048576)}')   # portabel (macOS und Linux)
if [ "$FREE_GB" -lt 40 ]; then
  LANES=1; WORKERS=5; export HF_CAPTURE_PARALLEL_STREAM=true
  echo "Nur $FREE_GB GB frei → 1 Spur im Stream-Modus."
elif [ "$FREE_GB" -lt 100 ] && [ "$LANES" -gt 2 ]; then
  LANES=2; WORKERS=5
  echo "Nur $FREE_GB GB frei → 2 Spuren."
fi
echo "Rendere mit $LANES Spur(en) × $WORKERS Worker ($FREE_GB GB frei)."

render_one() {
  id=$1; workers=$2
  [ -f "$W/renders/$id.mp4" ] && return
  cd "$W/segs/$id" && nice -n 10 npx hyperframes render . -o "$W/renders/$id.tmp.mp4" --resolution 4k \
    --video-bitrate 60M --fps 30 --workers "$workers" --quiet > "$W/renders/$id.log" 2>&1 \
    && mv "$W/renders/$id.tmp.mp4" "$W/renders/$id.mp4" && echo "OK $id" || echo "FAIL $id"
}
export -f render_one; export W
# Längste Segmente zuerst, damit am Ende kein langes Segment allein läuft.
ids=$(python3 -c "import json;print(' '.join(m['id'] for m in sorted(json.load(open('manifest.json')), key=lambda m: -m['dur'])))")
printf '%s\n' $ids | xargs -P "$LANES" -I{} bash -c "render_one {} $WORKERS"
# Nachlauf: einzeln, weniger Worker
for id in $ids; do [ -f "$W/renders/$id.mp4" ] || render_one $id 3; done
rm -rf "$W"/renders/work-* "$W"/renders/*.tmp.mp4
# Vollständigkeit prüfen
python3 - <<'EOF'
import json, subprocess
bad = []
for m in json.load(open('manifest.json')):
    r = subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v:0', '-show_entries',
                        'stream=nb_read_packets,width', '-of', 'csv=p=0', f'renders/{m["id"]}.mp4'], capture_output=True, text=True)
    try:
        w, n = r.stdout.strip().split(',')
        ok = int(w) == 3840 and abs(int(n) - round(m['dur'] * 30)) <= 1
    except Exception:
        ok = False
    if not ok: bad.append(m['id'])
print('ALLDONE', 'alle Segmente vollständig' if not bad else f'FEHLEN/DEFEKT: {bad}')
EOF
