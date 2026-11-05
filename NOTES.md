# NOTES

Session start: Thu Nov  5 06:06:47 UTC 2026 (time limit 2 hours, stop new work at 07:51 UTC).

## Decisions

- Step 1: this repo had no commits. The upstream `development` branch (393 commits, head `c63d721a`) was fetched and
  checked out directly, so `--allow-unrelated-histories` was not needed. `docs` and `res/battle-breakers-data` stay
  submodules at upstream commits `a41de78` and `03d05ca`.
- Step 2: no game client files were downloaded. The repo contains 43,464 `.manifest` files under `res/wex`
  (chunk metadata, no PAK data). No `.pak`, `.apk`, `.ipa` or `.obb` files exist in the tree.
- Step 3: MongoDB 8.0.4 was installed here from the official `mongodb-linux-x86_64-ubuntu2404-8.0.4.tgz` tarball and
  run with `mongod --dbpath /opt/mongo-data --fork`. mongomock was not needed. On a Mac, `setup-mac.sh` uses Homebrew
  `mongodb-community`.
- Step 3: `uv sync` installed Python 3.14.6, because `.python-version` pins 3.14. No dependency changes.
- Step 3: the only startup blocker was a missing RSA key pair. `utils/utils.py` exits when
  `utils/crypto/bb_private_key.pem` or `bb_public_key.pem` is missing. Both files are gitignored. Fix: run the two
  upstream scripts `utils/crypto/create private key.py` and `create public key.py` (password `pw` from
  `key_config.py`). No server code changed. `setup-mac.sh` runs them when the files are missing.
- Step 3: `uv run sanic main:app` binds 127.0.0.1:8000 (Sanic CLI defaults). `[server] host/port` in `utils/config.toml`
  only apply to `python main.py`. `[server] domain` is substituted into the cloud storage hotfix files
  (`res/wex/api/cloudstorage/system/DefaultEngine.ini` and `DefaultGame.ini`), so it should match the URL the client uses.
- Step 3: Python 3.14 prints `SyntaxWarning` and `DeprecationWarning` lines from Sanic and asyncio at startup. They are harmless.
