# HANDOFF

## Steps done

1. Upstream imported with history, submodules kept, README credit added.

2. No client files downloaded (see NOTES.md).
3. Server starts against a real MongoDB 8.0.4 after generating the RSA key pair.

4. `tests/smoke_test.py`: 29/29 checks pass at step 4 (login, QueryProfile, InitializeLevel, FinalizeLevel).

5. FALLBACK level generator behind `[levels] fallback-generator = "True"` in `utils/config.toml`. Smoke tests: 42/42.

6. `scripts/setup-mac.sh` and `scripts/run-mac.sh`, both tested twice (setup with a fake brew shim).

## Next step

7. `scripts/make-client-config.py` writing Engine.ini and Game.ini for Windows and Android paths.

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
