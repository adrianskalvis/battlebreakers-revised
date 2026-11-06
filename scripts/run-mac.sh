#!/usr/bin/env bash
# Starts the Breakers Revived server on http://127.0.0.1:8000 (override with HOST=... PORT=...).
# Makes sure MongoDB is running first. If the port is already serving, it reports that and exits 0,
# so running this script twice is safe.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
# Same Python as setup-mac.sh; without this, uv run would rebuild the venv on the 3.14 pin.
export UV_PYTHON="${UV_PYTHON:-3.12}"

if ! command -v brew >/dev/null 2>&1; then
  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    [[ -x "$candidate" ]] && eval "$("$candidate" shellenv)" && break
  done
fi

if [[ ! -f utils/crypto/bb_private_key.pem || ! -d res/battle-breakers-data/WorldExplorers ]]; then
  echo "Missing keys or game data. Run scripts/setup-mac.sh first." >&2
  exit 1
fi

if command -v brew >/dev/null 2>&1 && brew list --formula mongodb-community >/dev/null 2>&1; then
  if ! brew services list | awk '$1=="mongodb-community" {print $2}' | grep -q '^started$'; then
    echo "Starting mongodb-community service"
    brew services start mongodb-community
  fi
fi

if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  if curl -fsS --max-time 3 "http://127.0.0.1:$PORT/lightswitch/api/version" 2>/dev/null | grep -q '"lightswitch"'; then
    echo "Breakers Revived is already running: http://$HOST:$PORT"
    exit 0
  fi
  echo "Port $PORT is used by another program. Nothing was stopped:" >&2
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >&2 || true
  echo "Use a free port: PORT=8010 scripts/run-mac.sh" >&2
  echo "Then set [server] domain = \"http://127.0.0.1:8010\" in utils/config.toml to match." >&2
  exit 1
fi

echo "Starting Breakers Revived on http://$HOST:$PORT (Ctrl+C to stop)"
exec uv run sanic main:app --host "$HOST" --port "$PORT"
