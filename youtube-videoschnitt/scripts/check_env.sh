#!/bin/bash
# Prüft und richtet die Werkzeuge ein. Mehrfach ausführbar (idempotent).
# Getestet auf macOS (Apple Silicon) mit Homebrew. Linux geht grundsätzlich auch (libx264 statt Hardware-Encoder),
# dann Python 3.12 und ffmpeg über den Paketmanager installieren.
set -u
SK="$(cd "$(dirname "$0")/.." && pwd)"
CACHE=~/.cache/youtube-videoschnitt
mkdir -p "$CACHE"
ok() { echo "✓ $1"; }
bad() { echo "✗ $1"; }

command -v ffmpeg >/dev/null && ok "ffmpeg $(ffmpeg -version | head -1 | cut -d' ' -f3)" || bad "ffmpeg fehlt (Version 7 oder neuer) → brew install ffmpeg"
ffmpeg -hide_banner -encoders 2>/dev/null | grep -q h264_videotoolbox && ok "Hardware-Encoder h264_videotoolbox" || echo "• Kein h264_videotoolbox – es wird libx264 genutzt (langsamer, gleiche Qualität)"
command -v node >/dev/null && ok "node $(node --version)" || bad "node fehlt (>=22) → brew install node"
npx -y hyperframes --version >/dev/null 2>&1 && ok "hyperframes $(npx hyperframes --version 2>/dev/null)" || bad "hyperframes nicht startbar → npx -y hyperframes doctor"
python3 -c "import numpy" 2>/dev/null && ok "python3 + numpy" || bad "numpy fehlt für python3 → python3 -m pip install --user numpy"

# Whisper-Modell: ein vorhandenes large-v3-turbo (z. B. aus der Vibe-App) wiederverwenden statt 3 GB zu laden
MD=~/.cache/hyperframes/whisper/models
mkdir -p "$MD"
TURBO="$HOME/Library/Application Support/github.com.thewh1teagle.vibe/ggml-large-v3-turbo.bin"
if [ ! -e "$MD/ggml-large-v3.bin" ] && [ -f "$TURBO" ]; then ln -sf "$TURBO" "$MD/ggml-large-v3.bin"; fi
[ -e "$MD/ggml-large-v3.bin" ] && ok "Whisper-Modell large-v3(-turbo)" || echo "• Whisper-Modell wird beim ersten Transkribieren geladen (~3 GB, dauert)"

# Python-Umgebung für Musik (MusicGen), Mix, Zusammenbau und Schriften (Python 3.12 + torch + transformers + fonttools + Pillow)
VENV="$CACHE/mgenv"
PY312=$(command -v python3.12 || echo /opt/homebrew/bin/python3.12)
if [ ! -x "$VENV/bin/python" ]; then
  echo "• Richte Python-Umgebung ein (einmalig, ~2 GB) …"
  [ -x "$PY312" ] || brew install python@3.12 >/dev/null
  PY312=$(command -v python3.12 || echo /opt/homebrew/bin/python3.12)
  "$PY312" -m venv "$VENV" && "$VENV/bin/python" -m pip install -q --upgrade pip && \
  "$VENV/bin/python" -m pip install -q torch torchaudio transformers soundfile numpy scipy accelerate fonttools pillow
fi
"$VENV/bin/python" -c "import fontTools, PIL" 2>/dev/null || "$VENV/bin/python" -m pip install -q fonttools pillow
"$VENV/bin/python" -c "import torch,transformers,soundfile,scipy,fontTools,PIL" 2>/dev/null && ok "Python-Umgebung ($VENV)" || bad "Python-Umgebung defekt – Ordner $VENV löschen und neu starten"
# Hinweis: pip immer als "$VENV/bin/python -m pip" aufrufen – nach Verschieben zeigt bin/pip auf den alten Pfad.

# Profil
python3 "$SK/scripts/profil.py" || true

# Bildgenerator laut Profil
GEN=$(python3 -c "import sys;sys.path.insert(0,'$SK/scripts');import profil as P;print(P.get('bilder.generator','keiner'))" 2>/dev/null)
if [ "$GEN" = "codex" ]; then
  CODEX=$(python3 -c "import sys;sys.path.insert(0,'$SK/scripts');import profil as P;print(P.codex_path() or '')" 2>/dev/null)
  [ -n "$CODEX" ] && ok "Codex-CLI ($CODEX)" || bad "Codex-CLI nicht gefunden – find /Applications/ChatGPT.app -name codex -type f, Pfad in profil.json → bilder.codex_pfad"
else
  echo "• Bildgenerator: ${GEN:-keiner} (Icons ohne eigene Dateien werden als Linien-Icons gezeichnet)"
fi

FREE=$(df -g ~ 2>/dev/null | tail -1 | awk '{print $4}')
[ -n "$FREE" ] && { [ "$FREE" -gt 60 ] && ok "Freier Speicher: ${FREE} GB" || bad "Nur ${FREE} GB frei – ein 30-Min-4K-Projekt braucht ~25–30 GB Arbeitsfläche"; }
