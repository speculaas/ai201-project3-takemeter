#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
echo "Local:   http://127.0.0.1:${PORT}"
if [[ -n "${LAN_IP}" ]]; then
  echo "Network: http://${LAN_IP}:${PORT}  (other devices on your Wi‑Fi/LAN)"
fi
echo "Stop with Ctrl+C. No login — only use on a network you trust."
echo

exec uvicorn main:app --reload --host "${HOST}" --port "${PORT}"
