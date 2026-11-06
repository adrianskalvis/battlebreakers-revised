#!/usr/bin/env bash
# Breakers Revived server setup for macOS (Apple Silicon or Intel).
# Installs Homebrew, uv and MongoDB Community, starts MongoDB as a brew service, fetches the two submodules,
# installs Python dependencies with uv and creates the server RSA key pair.
# Every step checks first, so running this script twice is safe.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Python 3.12 has prebuilt macOS wheels for every locked dependency. Under the 3.14 pin in .python-version,
# faust-cchardet has no macOS wheel and needs a compiler. Override with UV_PYTHON=3.14 if wanted.
export UV_PYTHON="${UV_PYTHON:-3.12}"

say() { printf '\n==> %s\n' "$*"; }

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Warning: this script targets macOS. Detected $(uname -s); continuing anyway." >&2
fi

# 1. Homebrew
if ! command -v brew >/dev/null 2>&1; then
  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    [[ -x "$candidate" ]] && eval "$("$candidate" shellenv)" && break
  done
fi
if ! command -v brew >/dev/null 2>&1; then
  say "Installing Homebrew (asks for your Mac password once)"
  # In NONINTERACTIVE mode the installer cannot ask for the sudo password itself, so cache it here first.
  sudo -v
  NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    [[ -x "$candidate" ]] && eval "$("$candidate" shellenv)" && break
  done
else
  say "Homebrew found: $(command -v brew)"
fi

# 2. uv
if ! command -v uv >/dev/null 2>&1; then
  say "Installing uv"
  brew install uv
else
  say "uv found: $(uv --version)"
fi

# 3. MongoDB Community
if ! brew list --formula mongodb-community >/dev/null 2>&1; then
  say "Installing mongodb-community"
  brew tap mongodb/brew
  # Homebrew 6 refuses formulae from third-party taps until trusted. Trust only the two formulae it installs (mongodb-community and its dependency mongodb-database-tools).
  if brew commands --quiet 2>/dev/null | grep -qx trust; then
    brew trust --formula mongodb/brew/mongodb-community
    brew trust --formula mongodb/brew/mongodb-database-tools
  fi
  brew install mongodb-community
else
  say "mongodb-community already installed"
fi
if brew services list | awk '$1=="mongodb-community" {print $2}' | grep -q '^started$'; then
  say "mongodb-community service already started"
else
  say "Starting mongodb-community service"
  brew services start mongodb-community
fi

# 4. Submodules (docs and res/battle-breakers-data). Server code needs res/battle-breakers-data.
say "Fetching submodules"
git submodule update --init

# 5. Python dependencies (uv also installs the Python version pinned in .python-version)
say "Running uv sync"
uv sync

# 6. Server RSA key pair, used to sign tokens. Both files are gitignored.
if [[ ! -f utils/crypto/bb_private_key.pem ]]; then
  say "Creating utils/crypto/bb_private_key.pem"
  (cd utils/crypto && uv run python "create private key.py")
  rm -f utils/crypto/bb_public_key.pem
fi
if [[ ! -f utils/crypto/bb_public_key.pem ]]; then
  say "Creating utils/crypto/bb_public_key.pem"
  (cd utils/crypto && uv run python "create public key.py")
fi

say "Setup complete. Start the server with: scripts/run-mac.sh"
