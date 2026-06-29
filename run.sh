#!/usr/bin/env bash
# VOD Studio - run (Linux / macOS). Windows: use run.bat
set -e
cd "$(dirname "$0")"

PORT="${PORT:-7000}"
if [ ! -x venv/bin/python ]; then echo "[ERROR] venv not found. Run ./setup.sh first."; exit 1; fi
export AUTH_ENABLED="${AUTH_ENABLED:-false}"

echo "============================================================"
echo "  VOD Studio - starting"
echo "  URL: http://127.0.0.1:$PORT/vodstudio"
echo "  (Ctrl+C to stop)"
echo "============================================================"

# open browser after a short delay (best-effort)
( sleep 4
  if command -v xdg-open >/dev/null 2>&1; then xdg-open "http://127.0.0.1:$PORT/vodstudio"
  elif command -v open >/dev/null 2>&1; then open "http://127.0.0.1:$PORT/vodstudio"; fi ) >/dev/null 2>&1 &

exec venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port "$PORT"
