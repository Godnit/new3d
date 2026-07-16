#!/usr/bin/env bash
set -euxo pipefail

adb install -r build/CityQuest3D-Emulator.apk
adb shell settings put secure immersive_mode_confirmations confirmed || true

adb logcat -c
adb shell monkey -p com.godnit.cityquest3dlegacy -c android.intent.category.LAUNCHER 1
sleep 15

adb shell pidof com.godnit.cityquest3dlegacy | tr -d '\r' > /tmp/cityquest.pid
test -s /tmp/cityquest.pid

# The new build enters gameplay directly. Capture the initial playable view,
# move the virtual joystick forward, then capture a second changed frame.
adb exec-out screencap -p > build/android81-menu.png
adb shell input swipe 240 830 240 650 1400
sleep 5
adb exec-out screencap -p > build/android81-game.png

adb logcat -d > build/android81-logcat.txt
if grep -E "FATAL EXCEPTION|Fatal signal|Process: com.godnit.cityquest3dlegacy.*has died|ANR in com.godnit.cityquest3dlegacy" build/android81-logcat.txt; then
    exit 1
fi

python3 tools/validate_android_screens.py
cp build/android81-game.png build/CityQuest3D-Legacy-Preview.png
