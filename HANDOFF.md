# HANDOFF

## Steps done

1. Upstream imported with history, submodules kept, README credit added.

2. No client files downloaded (see NOTES.md).
3. Server starts against a real MongoDB 8.0.4 after generating the RSA key pair.

4. `tests/smoke_test.py`: 29/29 checks pass at step 4 (login, QueryProfile, InitializeLevel, FinalizeLevel).

5. FALLBACK level generator behind `[levels] fallback-generator = "True"` in `utils/config.toml`. Smoke tests: 42/42.

6. `scripts/setup-mac.sh` and `scripts/run-mac.sh`, both tested twice (setup with a fake brew shim).

7. `scripts/make-client-config.py` writes Engine.ini/Game.ini for Windows and 3 Android paths. Output matches the
   server's hotfix files. Extra per-service keys are unverified (NOTES.md).

8. MAC.md written.

9. Final push and summary (below).

## Next step

None from the task list. Optional follow-ups: run `scripts/setup-mac.sh` on a real Mac, try a real client with
`scripts/make-client-config.py`, and capture more level data to replace fallback levels.

## Summary

### What works

- The upstream server (393 commits, `development` head `c63d721a`) is imported with history. `docs` and
  `res/battle-breakers-data` stay submodules. LICENSE is unchanged. README credits Alexander Hanson (dippyshere).
- `uv sync` plus `uv run sanic main:app` starts the server on 127.0.0.1:8000 against MongoDB 8.0.4, once the RSA key
  pair exists. `scripts/setup-mac.sh` creates the keys.
- Three upstream bugs fixed with one-line changes: profiles lacked `profileId`, FinalizeLevel nested its notification
  list, and `LTG.Completion.Dark.Medium.json` was invalid JSON (HTTP 500 on Dark levels).
- FALLBACK level generator for the levels without captured data, behind `[levels] fallback-generator = "True"`.
- `scripts/setup-mac.sh`, `scripts/run-mac.sh`, `scripts/make-client-config.py`, `MAC.md`.

### What is tested

- `tests/smoke_test.py`: 42/42 checks pass against a live server and real MongoDB. It covers signup, oauth token
  (authorization_code, exchange_code, password), QueryProfile profile0 and levels, InitializeLevel and FinalizeLevel
  for 2 captured levels and 1 fallback level, compared to the docs submodule examples.
- Flag off: fallback level gets the upstream single room (2 expected failures, 40/42).
- `run-mac.sh` run twice on Linux: second run exits 0 with "already in use".
- `setup-mac.sh` run twice on Linux with a fake `brew`: run 1 installs and starts, run 2 skips. Key generation path
  tested by deleting the keys.
- `make-client-config.py --no-unverified` output equals the server's served hotfix files byte for byte.

### What is unverified

- Nothing ran on a real Mac; Homebrew, `mongodb-community` and `brew services` were simulated.
- No game client was used. Whether any client reads the generated Engine.ini/Game.ini is unverified.
- The 9 extra `[OnlineSubsystemMcp.*ServiceMcp]` sections in the generated Engine.ini (list in NOTES.md).
- Fallback room and reward amounts are estimates, not captured data.
- CrossOver, Parallels, Android emulator and iOS-on-Mac steps in MAC.md.

## Resume commands

On a Mac:

```bash
git clone --recurse-submodules -b claude/wizardly-volta-ifbm7m https://github.com/adrianskalvis/battlebreakers-revised.git
cd battlebreakers-revised
scripts/setup-mac.sh
scripts/run-mac.sh
# second terminal:
uv run python tests/smoke_test.py
```

Manual (any OS):

```bash
git clone --recurse-submodules -b claude/wizardly-volta-ifbm7m https://github.com/adrianskalvis/battlebreakers-revised.git
cd battlebreakers-revised
git submodule update --init
uv sync
(cd utils/crypto && uv run python "create private key.py" && uv run python "create public key.py")
# start MongoDB (Mac: brew services start mongodb-community), then:
uv run sanic main:app
# second terminal:
uv run python tests/smoke_test.py
```
