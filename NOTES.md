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
- Step 4: `tests/smoke_test.py` runs against a live server with the standard library only. It parses the
  `### Request Body` and `### Response Body` JSON blocks from the docs submodule pages for `oauth/token`,
  `QueryProfile(profile0)`, `QueryProfile(levels)`, `InitializeLevel` and `FinalizeLevel`, replays the requests and
  compares keys. The docs hero ids belong to the capture account, so the test swaps in heroes from the new account.
  The test sends the current `rvn`, like the client, so the server returns deltas. 29/29 checks pass.
- Step 4 fix 1: `utils/profile_system.py` serialised profiles with `profileType` only. Captured responses use
  `profileId`. Smallest fix: emit both keys. `profileType` stays, so stored MongoDB documents keep working.
- Step 4 fix 2: `api/wex/profile/finalize_level.py` appended a list to the notifications list, giving
  `"notifications": [[{...}]]`. Captured response is `[{...}]`. Fix: pass the dict `level_complete_notification[0]`.
- Step 4 finding, not fixed: `LTG.Chest.Fire.VeryHigh`, `LTG.Chest.Fire.High` and `LTG.Completion.Light.Medium` are
  missing from the loot tier group data, so FinalizeLevel logs `Failed to find loot tier group` and skips that loot.
  This is an upstream data gap.
