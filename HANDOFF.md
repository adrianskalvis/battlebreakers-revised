# HANDOFF

## Steps done

1. Upstream imported with history, submodules kept, README credit added.

2. No client files downloaded (see NOTES.md).
3. Server starts against a real MongoDB 8.0.4 after generating the RSA key pair.

## Next step

4. Smoke tests from docs submodule examples for login, QueryProfile, InitializeLevel, FinalizeLevel.

## Resume commands

```bash
git clone --recurse-submodules -b claude/wizardly-volta-ifbm7m https://github.com/adrianskalvis/battlebreakers-revised.git
cd battlebreakers-revised
git submodule update --init
uv sync
(cd utils/crypto && uv run python "create private key.py" && uv run python "create public key.py")
# start MongoDB (Mac: brew services start mongodb-community), then:
uv run sanic main:app
```
