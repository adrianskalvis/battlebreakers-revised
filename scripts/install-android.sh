#!/usr/bin/env bash
# Installs your own Battle Breakers APK on the running Android emulator and points it at this server.
# Usage: scripts/install-android.sh /path/to/your.apk
# Needs: a running emulator (adb devices lists it) and the server on 127.0.0.1:8000 (scripts/run-mac.sh).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

APK="${1:-}"
PKG=com.chairentertainment.BattleBreakers
URL="http://127.0.0.1:8000"

[ -f "$APK" ] || { echo "Give the path to your APK: scripts/install-android.sh ~/Downloads/your.apk" >&2; exit 1; }
adb get-state >/dev/null 2>&1 || { echo "No emulator found. Start one in Android Studio first." >&2; exit 1; }

echo "==> Forwarding emulator port 8000 to this Mac"
adb reverse tcp:8000 tcp:8000

echo "==> Installing $APK"
adb install -r "$APK"

echo "==> Writing config files for $URL"
python3 scripts/make-client-config.py "$URL" >/dev/null

push() { # $1 = path on the device
  adb shell mkdir -p "'$1'"
  adb push "client-config/android$1/Engine.ini" "client-config/android$1/Game.ini" "$1/" >/dev/null
  echo "    copied to $1"
}
echo "==> Copying config files into the emulator"
push "/storage/emulated/0/Android/data/$PKG/files/Saved/Config/Android"
push "/sdcard/UE4Game/WorldExplorers/Saved/Config/Android"
if adb root >/dev/null 2>&1 && adb wait-for-device; then
  adb reverse tcp:8000 tcp:8000 >/dev/null # adb root restarts adbd, which clears the forwarding
  push "/data/data/$PKG/files/Saved/Config/Android"
else
  echo "    skipped /data/data (this emulator image does not allow adb root)"
fi

echo "==> Starting Battle Breakers"
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 >/dev/null
echo "Done. Log in inside the game. Rerun 'adb reverse tcp:8000 tcp:8000' after every emulator restart."
