#!/usr/bin/env bash
set -euxo pipefail

adb install -r build/CityQuest3D-Emulator.apk

# Android 8.1 shows a one-time system help overlay the first time an app enters
# immersive mode. Suppress only that emulator tutorial so the screenshots show
# the actual game menu and gameplay rather than the operating-system overlay.
adb shell settings put secure immersive_mode_confirmations confirmed || true

adb logcat -c
adb shell monkey -p com.godnit.cityquest3dlegacy -c android.intent.category.LAUNCHER 1
sleep 22

adb shell pidof com.godnit.cityquest3dlegacy | tr -d '\r' > /tmp/cityquest.pid
test -s /tmp/cityquest.pid

adb exec-out screencap -p > build/android81-menu.png

# The game menu supports Enter, which is more reliable than model-dependent
# touch coordinates in the Android emulator.
adb shell input keyevent 66
sleep 10
adb exec-out screencap -p > build/android81-game.png

adb logcat -d > build/android81-logcat.txt
if grep -E "FATAL EXCEPTION|Fatal signal|Process: com.godnit.cityquest3dlegacy.*has died|ANR in com.godnit.cityquest3dlegacy" build/android81-logcat.txt; then
    exit 1
fi

python3 tools/validate_android_screens.py
cp build/android81-game.png build/CityQuest3D-Legacy-Preview.png
