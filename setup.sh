#!/usr/bin/env bash
# VOD Studio - setup (Linux / macOS). Windows: use setup.bat
set -e
cd "$(dirname "$0")"

echo "============================================================"
echo "  VOD Studio - setup (Linux / macOS)"
echo "============================================================"

# 1) Python 3.11+
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then echo "[ERROR] Python 3.11+ required (https://www.python.org/downloads/)"; exit 1; fi
echo "[OK] Python: $PY"

# 2) venv
if [ ! -x venv/bin/python ]; then echo "[1/5] creating venv..."; "$PY" -m venv venv; else echo "[1/5] venv exists - skipping"; fi
VPY="venv/bin/python"

# 3) libraries
echo "[2/5] installing libraries... (first run takes a few minutes)"
"$VPY" -m pip install --upgrade pip
"$VPY" -m pip install -r requirements.txt
# notebooklm-mcp-cli pulls urllib3-future which shadows urllib3 and breaks fastembed/requests.
echo "[3/5] restoring urllib3 (protects fastembed/requests)..."
"$VPY" -m pip install --force-reinstall --no-deps "urllib3==2.7.0"

# 4) Codex CLI (ChatGPT login, needs Node) - optional
echo "[4/5] checking codex (ChatGPT) ..."
if ! command -v codex >/dev/null 2>&1; then
  if command -v npm >/dev/null 2>&1; then npm i -g @openai/codex || true
  else echo "  [note] install Node.js + 'npm i -g @openai/codex' for ChatGPT login"; fi
fi

# 5) local TTS model (~380MB) + mp4maker + .env
echo "[5/6] TTS model + mp4maker ..."
if [ ! -f assets/onnx/vocoder.onnx ]; then "$VPY" scripts/setup_assets.py; else echo "  [OK] TTS model present"; fi
# mp4maker is vendored in this repo (no clone needed)
[ -f .env ] || { [ -f .env.example ] && cp .env.example .env; }

# 6) install PPTX fonts (Black Han Sans / Do Hyeon) for current user
echo "[6/6] installing PPTX fonts (assets/fonts) ..."
"$VPY" scripts/install_fonts.py || echo "  [note] font install skipped"

echo
echo "Note: ffmpeg/ffprobe must be on PATH for video render (macOS: 'brew install ffmpeg' · Debian/Ubuntu: 'sudo apt install ffmpeg')."
echo "Setup complete. Next: ./run.sh   (in the app, ChatGPT login: 'codex login')"
