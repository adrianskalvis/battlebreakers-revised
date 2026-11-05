# NOTES

Session start: Thu Nov  5 06:06:47 UTC 2026 (time limit 2 hours, stop new work at 07:51 UTC).

## Decisions

- Step 1: this repo had no commits. The upstream `development` branch (393 commits, head `c63d721a`) was fetched and
  checked out directly, so `--allow-unrelated-histories` was not needed. `docs` and `res/battle-breakers-data` stay
  submodules at upstream commits `a41de78` and `03d05ca`.
- Step 2: no game client files were downloaded. The repo contains 43,464 `.manifest` files under `res/wex`
  (chunk metadata, no PAK data). No `.pak`, `.apk`, `.ipa` or `.obb` files exist in the tree.
