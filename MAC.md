# Running Breakers Revived on a Mac

This guide covers the server on macOS (Apple Silicon or Intel) and the known ways to run a Battle Breakers client
against it. The server is the upstream [Breakers Revived](https://github.com/Breakers-Revived/battle-breakers-private-server)
work by Alexander Hanson (dippyshere). This repo adds Mac scripts, smoke tests and a labelled fallback level generator.
Decisions and unverified items are in [NOTES.md](NOTES.md).

This repo does not include or download any game client, APK, IPA or PAK file. You need your own copy of the game.

## Quick start

Paste into Terminal once:

```bash
git clone --recurse-submodules -b claude/wizardly-volta-ifbm7m https://github.com/adrianskalvis/battlebreakers-revised.git ~/battlebreakers-revised && open ~/battlebreakers-revised/Start-Battle-Breakers.command
```

After that, double-click `Start-Battle-Breakers.command` in the `battlebreakers-revised` folder to start the server.
It runs setup (skipping finished steps), then the server, in its own Terminal window.

## 1. Setup

```bash
git clone --recurse-submodules -b claude/wizardly-volta-ifbm7m https://github.com/adrianskalvis/battlebreakers-revised.git
cd battlebreakers-revised
scripts/setup-mac.sh
```

`scripts/setup-mac.sh` does the following, skipping any step that is already done:

1. Installs Homebrew if `brew` is missing.
2. Installs `uv` with Homebrew if it is missing.
3. Taps `mongodb/brew`, installs `mongodb-community` and runs `brew services start mongodb-community`.
4. Runs `git submodule update --init` for `docs` and `res/battle-breakers-data`.
5. Runs `uv sync` with Python 3.12 (`UV_PYTHON=3.12`), because every dependency has a prebuilt macOS wheel for
   3.12. Under the 3.14 pin in `.python-version`, `faust-cchardet` would need compiling.
6. Creates `utils/crypto/bb_private_key.pem` and `bb_public_key.pem`. The server exits at startup without them.

Run it again at any time. A second run changes nothing.

## 2. Running the server

```bash
scripts/run-mac.sh
```

The server listens on `http://127.0.0.1:8000`. Stop it with Ctrl+C. If Breakers Revived already runs on the port,
the script says so and exits 0. If another program holds the port, the script lists it, stops nothing, and exits 1;
then use `PORT=8010 scripts/run-mac.sh` and set `[server] domain` in `utils/config.toml` to the same port.

For a client on another device (VM, emulator, phone), listen on all interfaces:

```bash
HOST=0.0.0.0 scripts/run-mac.sh
```

Then set `[server] domain` in `utils/config.toml` to the URL that device uses, for example `http://192.168.1.20:8000`.
The server sends that value to clients inside its cloud storage hotfix files. Find the Mac's LAN address with:

```bash
ipconfig getifaddr en0
```

macOS may ask to allow incoming connections for Python the first time. Allow it.

### Smoke tests

With the server running, in a second terminal:

```bash
uv run python tests/smoke_test.py
```

It creates a throwaway account, then checks login, QueryProfile (profile0, levels), InitializeLevel and FinalizeLevel
against the captured examples in the `docs` submodule. 42 checks pass at the time of writing.

### Fallback levels

Most levels have no captured room and loot data upstream. With `[levels] fallback-generator = "True"` (default) in
`utils/config.toml`, such levels get estimated rooms and rewards built from the LevelInfo datatable, so the map keeps
unlocking. Captured data always wins. The server log prints `FALLBACK level generator used for <level>` each time.
Set the flag to `"False"` for the upstream single placeholder room.

## 3. Pointing a client at the server

```bash
python3 scripts/make-client-config.py http://192.168.1.20:8000
```

This writes `Engine.ini` and `Game.ini` under `client-config/` for:

- Windows: `%LOCALAPPDATA%\WorldExplorers\Saved\Config\WindowsNoEditor\`
- Android: `/storage/emulated/0/Android/data/com.chairentertainment.BattleBreakers/files/Saved/Config/Android/`
- Android: `/sdcard/UE4Game/WorldExplorers/Saved/Config/Android/`
- Android: `/data/data/com.chairentertainment.BattleBreakers/files/Saved/Config/Android/`

It also prints `adb push` commands. The confirmed keys are the ones the server already sends as hotfixes. A few extra
per-service keys are unverified; `--no-unverified` leaves them out. See NOTES.md.

## 4. Ways to run the game on a Mac

None of these paths was tested with a real client in this session.

### Windows build in CrossOver

1. Create a Windows 10 64-bit bottle and install your Windows copy of Battle Breakers in it.
2. The bottle shares the Mac's network, so `http://127.0.0.1:8000` works. Generate the files:

   ```bash
   python3 scripts/make-client-config.py http://127.0.0.1:8000
   ```

3. Copy `client-config/windows/WorldExplorers/Saved/Config/WindowsNoEditor/*.ini` into the bottle's
   `drive_c/users/<user>/AppData/Local/WorldExplorers/Saved/Config/WindowsNoEditor/`. CrossOver's
   "Open C: Drive" menu item opens the bottle's `drive_c`.

On Apple Silicon, CrossOver runs the x86-64 game through Rosetta 2. Performance and graphics compatibility are unknown.

### Windows build in Parallels Desktop

1. Install Windows 11 (ARM on Apple Silicon; it emulates x64 apps) and the game inside the VM.
2. Run the server with `HOST=0.0.0.0 scripts/run-mac.sh`.
3. The VM reaches the Mac at its LAN address, or at the host address of the Parallels shared network
   (`ipconfig getifaddr bridge100` on the Mac, usually). Use that in `make-client-config.py` and `[server] domain`.
4. Copy the Windows ini files to `%LOCALAPPDATA%\WorldExplorers\Saved\Config\WindowsNoEditor\` in the VM.

### Android build in an emulator

1. Install Android Studio and create an emulator. On Apple Silicon use an arm64 system image. A "Google APIs" image
   (no Play Store) allows `adb root`, which the `/data/data/...` path needs.
2. Install your APK with `adb install <your.apk>`.
3. The emulator reaches the Mac at `10.0.2.2`. Run:

   ```bash
   python3 scripts/make-client-config.py http://10.0.2.2:8000
   ```

   Then run the printed `adb` commands and set `[server] domain = "http://10.0.2.2:8000"`.
4. Alternative from README.md: the Breakers Revived fork of
   [Sinum](https://github.com/Breakers-Revived/Sinum-BattleBreakers), applied with
   [AndroidPatcherCLI](https://github.com/Breakers-Revived/AndroidPatcherCLI), redirects the game's Epic URLs in native
   code instead of using ini files.

Which of the three Android paths a client reads depends on its version. The script writes all three.

### iOS build on Apple Silicon

Apple Silicon Macs can run iPhone apps. A Battle Breakers IPA must be decrypted and re-signed before macOS will run it,
for example with a sideloading tool such as PlayCover. README.md says:

- The patched Breakers Revived IPA is preconfigured. Override the server with an `api_url.txt` file containing
  `http://<host>:<port>` in the game's Documents directory.
- An unpatched client needs Engine.ini and Game.ini in `Documents/Saved/Config/iOS`, the fallback audio system in
  Engine.ini, and libicu64 bundled and relinked to avoid crashes on recent iOS.

On macOS, the Documents directory of an iPhone app usually lives under `~/Library/Containers/<container>/Data/Documents`.
`make-client-config.py` does not write the iOS path; copy the Windows `Engine.ini`/`Game.ini` there by hand.
Whether the game runs this way on macOS is unverified.

## 5. What is still missing upstream

From README.md and this session's testing:

- Captured level data exists for 68 level files. Most of the 1,546 LevelInfo rows have no captured rooms, enemies or
  loot. The fallback generator only estimates these.
- Loot tier groups `LTG.Chest.Fire.VeryHigh`, `LTG.Chest.Fire.High` and `LTG.Completion.Light.Medium` are missing, so
  FinalizeLevel skips that loot and logs an error.
- Not implemented: ClaimGiftPoints, SendGiftPoints (data lost), CollectHammerQuestEnergy, CollectHammerQuestRealtime,
  GenerateMatches, JoinMatchmaking, RefreshRunCount, and the friend gift part of GenerateDailyQuests.
- Partial: AbandonLevel, GenerateMatchWithFriend, PurchaseCatalogEntry, InitializeLevel, FinalizeLevel.
- Price Engine supports AUD only. Catalog and rotational content are frozen at the last week of December 2022.
- The Battle Breakers CDN service serves PAK files from `[content] build-manifest` and `chunk-v3` in
  `utils/config.toml`, which default to `D:/Battle Breakers/`. Clients that download content need your own files there.
- Upstream has no step-by-step client configuration guide. `scripts/make-client-config.py` fills part of that gap.
