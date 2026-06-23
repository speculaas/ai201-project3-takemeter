#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Default even if PORT/HOST are set to empty (e.g. some SSH/cloud shells).
HOST="${HOST-}"
PORT="${PORT-}"
[[ -z "${HOST}" ]] && HOST="0.0.0.0"
[[ -z "${PORT}" ]] && PORT="8000"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# .venv may exist but lack packages (new machine, interrupted install, etc.)
if ! python -m uvicorn --version &>/dev/null; then
  echo "Installing labeler dependencies..."
  python -m pip install -r requirements.txt
fi

LAN_IP=""
if command -v ipconfig &>/dev/null; then
  LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
elif command -v hostname &>/dev/null; then
  LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
fi

echo "Local:   http://127.0.0.1:${PORT}"
if [[ -n "${LAN_IP}" ]]; then
  echo "Network: http://${LAN_IP}:${PORT}  (other devices on your Wi‑Fi/LAN)"
fi
echo "Stop with Ctrl+C. No login — only use on a network you trust."
echo

exec python -m uvicorn main:app --reload --host "${HOST}" --port "${PORT}"
