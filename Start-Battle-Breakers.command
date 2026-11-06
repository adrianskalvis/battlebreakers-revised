#!/usr/bin/env bash
# Double-click this file in Finder. It runs scripts/setup-mac.sh (safe to repeat, skips finished steps),
# then starts the server in this Terminal window on http://127.0.0.1:8000. Close the window or press Ctrl+C to stop.
set -euo pipefail
cd "$(dirname "$0")"
scripts/setup-mac.sh
scripts/run-mac.sh
