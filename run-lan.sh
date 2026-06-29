#!/usr/bin/env bash
# VOD Studio - LAN mode (Linux / macOS) for internal UX feedback. Windows: run-lan.bat
set -e
cd "$(dirname "$0")"

PORT="${PORT:-7000}"
if [ ! -x venv/bin/python ]; then echo "[ERROR] venv not found. Run ./setup.sh first."; exit 1; fi
export AUTH_ENABLED="${AUTH_ENABLED:-false}"

# best-effort LAN IPv4 (Linux: hostname -I · macOS: ipconfig getifaddr en0)
IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
[ -z "$IP" ] && IP="$(ipconfig getifaddr en0 2>/dev/null || true)"
[ -z "$IP" ] && IP="<this-PC-IP>"

echo "============================================================"
echo "  VOD Studio - LAN mode (internal UX feedback)"
echo "  This PC:    http://127.0.0.1:$PORT/vodstudio"
echo "  Teammates:  http://$IP:$PORT/vodstudio"
echo "  (same Wi-Fi/LAN; allow through firewall if prompted · Ctrl+C to stop)"
echo "============================================================"

exec venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port "$PORT"
