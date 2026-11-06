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
- Step 5: upstream InitializeLevel already called `room_generator` for uncaptured levels, but it returned one room with
  150 gold. The new FALLBACK path (`fallback_level_generator` in `utils/utils.py`) runs only when no captured file
  exists for the level or any lower difficulty, and `[levels] fallback-generator = "True"` (default) in
  `utils/config.toml`. Setting it to `"False"` restores the upstream single room.
- Step 5 estimates (guesses, not captured data): one room per LevelInfo `NumExpectedRooms`, each from `room_generator`
  (room `Room.Standard.FindExit.Easy.R01`, no enemies). Each room drops `150 + 10 * BaseWorldLevel` gold and
  `10 + BaseWorldLevel` account XP. Battle pass XP is `150 * EventTier` (the captured BurnyVolcano.Map1.D4 run had 450
  at EventTier 3). FinalizeLevel grants `100 * BaseWorldLevel` gold when the LevelInfo `CompletionLoot` tier group
  yields nothing for a fallback level. First-clear unlocks (`WorldUnlock:Level`) work as upstream, so map progress
  continues.
- Step 5: the `Level:InProgress` item carries `debug_fallback: true|false`, beside the upstream `debug_*` attributes.
  The server log prints `FALLBACK level generator used for <level>` each time.
- Step 5 fix: `res/wex/api/game/v2/tier_groups/loot/LTG.Completion.Dark.Medium.json` had a `# TODO` comment, which is
  invalid JSON, so FinalizeLevel returned HTTP 500 for every Dark level. The comment was removed. All other JSON files
  under `res/wex` and `res/account` parse.
- Step 6: `scripts/setup-mac.sh` installs Homebrew (non-interactive official installer) only when `brew` is missing,
  installs `uv` with Homebrew only when missing, taps `mongodb/brew` and installs `mongodb-community` only when
  missing, starts the brew service only when it is not `started`, runs `git submodule update --init` and `uv sync`,
  and creates the RSA key pair only when the files are missing. Tested twice on Linux with a fake `brew` shim: run 1
  installs and starts, run 2 skips both, both exit 0. Not run on a real Mac in this session.
- Step 6: `scripts/run-mac.sh` starts MongoDB if needed, then `exec uv run sanic main:app --host 127.0.0.1 --port 8000`
  (`HOST`/`PORT` override). If the port is already listening it prints a message and exits 0. Tested twice here.
- Step 6: `[server] domain` default changed from upstream `http://192.168.0.45:8080` (the upstream author's LAN address)
  to `http://127.0.0.1:8000`, to match `run-mac.sh`. The cloud storage hotfix files send this value to the client.
  For a client on another device, set it to the Mac's LAN URL and run `HOST=0.0.0.0 scripts/run-mac.sh`.
- Step 7: `scripts/make-client-config.py <url>` copies `res/wex/api/cloudstorage/system/DefaultEngine.ini` and
  `DefaultGame.ini` and substitutes `{0}` exactly like `api/wex/cloud_storage.py` (host:port in Engine.ini, full URL in
  Game.ini). It writes both files for the Windows path and the three Android paths from README.md, and prints `adb`
  commands. With `--no-unverified`, the output matched the server's served hotfix files byte for byte (checked with
  curl against `/wex/api/cloudstorage/system/<uniqueFilename>`). No game client was available, so no client has read
  these files in this session.
- Step 7 key sources: `Breakers-Revived/Sinum-BattleBreakers` (both branches) and `Breakers-Revived/AndroidPatcherCLI`
  hold no ini keys. Sinum rewrites `*.ol.epicgames.com` URLs in native code. The docs submodule only lists the hotfix
  file names. So the repo's hotfix templates are the only confirmed source.

## Unverified ini keys

Confirmed (present in `res/wex/api/cloudstorage/system/*.ini`): `[OnlineSubsystemMcp.BaseServiceMcp]`,
`[OnlineSubsystemMcp.GameServiceMcp]`, `[OnlineSubsystemMcp.AccountManagement]`, `[OnlineSubsystemMcp.AccountServiceMcp]`
(`Protocol`, `Domain`), `[OnlineSubsystemMcp.AccountServiceMcp Prod]` and `[... GameDev]` (`RedirectUrl`),
`[OnlineSubsystemMcp.OnlineIdentityMcp]` URLs, and Game.ini `[/Script/WorldExplorers.WexpMcpAccount]`
`WebUpgradeEpicAccountUrl`. These are confirmed as what the server sends; whether a client honours them from a local
Engine.ini before the first hotfix is also unverified.

Unverified (appended by default, removed with `--no-unverified`). Names follow the UE4 OnlineSubsystemMcp layout and
appear nowhere in the repo, docs or Sinum:

- `[OnlineSubsystemMcp.LightswitchServiceMcp]` `Protocol`, `Domain`
- `[OnlineSubsystemMcp.FriendServiceMcp]` `Protocol`, `Domain`
- `[OnlineSubsystemMcp.PersonaServiceMcp]` `Protocol`, `Domain`
- `[OnlineSubsystemMcp.PresenceServiceMcp]` `Protocol`, `Domain`
- `[OnlineSubsystemMcp.EntitlementsServiceMcp]` `Protocol`, `Domain`
- `[OnlineSubsystemMcp.CatalogServiceMcp]` `Protocol`, `Domain`
- `[OnlineSubsystemMcp.EulaTrackingServiceMcp]` `Protocol`, `Domain`
- `[OnlineSubsystemMcp.PriceEngineServiceMcp]` `Protocol`, `Domain`
- `[OnlineSubsystemMcp.DataRouterServiceMcp]` `Protocol`, `Domain`

All services share one host because the server routes by path prefix (`/account`, `/wex`, `/lightswitch`, ...).
- Step 8: MAC.md written. CrossOver, Parallels, Android emulator and iOS-on-Apple-Silicon instructions come from
  README.md and general tool behaviour. None was tested with a real client. The CrossOver bottle path, the Parallels
  `bridge100` address and the macOS iPhone app container path are typical locations, unverified here.
- Step 9: with `fallback-generator = "False"`, AbandonedVillage.Map1.D1 got the upstream single room
  (`debug_roomcount: 1`) and the two fallback checks failed as expected (40/42). Back on `"True"`: 42/42.

Session end of work: Thu Nov  5 06:21 UTC 2026 (about 15 minutes used of the 2 hour limit).

## Mac follow-up (2026-11-06)

- `setup-mac.sh` and `run-mac.sh` now export `UV_PYTHON=3.12`. Every locked dependency has a macOS arm64 wheel for
  3.12. Under the 3.14 pin, `faust-cchardet` 2.1.19 has no macOS wheel and would need compiling. `.python-version`
  is unchanged, so upstream and Linux keep 3.14.
- `setup-mac.sh` runs `sudo -v` before the Homebrew installer. In `NONINTERACTIVE` mode the installer cannot ask for
  the password itself and fails without cached sudo.
- `run-mac.sh` now checks `/lightswitch/api/version` when the port is taken. Breakers Revived on the port: exit 0.
  Another program on the port: it lists the program, stops nothing, and exits 1.
- `Start-Battle-Breakers.command` runs setup then the server; double-click it in Finder.
- Tested on Linux with a fake `brew` and MongoDB 8.3.7 (conda-forge build): launcher start, smoke tests 42/42 on
  Python 3.12.3, second run exits 0, port held by `python3 -m http.server` exits 1 and leaves it running.
