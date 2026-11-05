# HANDOFF

## Steps done

1. Upstream imported with history, submodules kept, README credit added.

2. No client files downloaded (see NOTES.md).
3. Server starts against a real MongoDB 8.0.4 after generating the RSA key pair.

4. `tests/smoke_test.py`: 29/29 checks pass (login, QueryProfile, InitializeLevel, FinalizeLevel).

## Next step

5. Fallback rooms/rewards for levels without captured data, behind `[levels] fallback-generator` in `utils/config.toml`.

## Resume commands

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
