# City Quest 3D — Android

A complete small 3D city mission game built with Godot 4.6.3 and exported as a real Android APK.

## Gameplay

- Third-person movement, sprint and jump
- Touch controls designed for landscape phones
- Imported Kenney 3D buildings, cars and characters
- Enemy pursuit and melee combat
- Collectibles, health and four-stage mission flow
- Enter, drive and exit a car
- Pause, restart, win and lose states
- Offline after installation

## Build

The GitHub Actions workflow downloads the CC0 3D packs, imports them through Godot, exports a signed APK, installs it in an Android emulator, launches it, checks the process/logcat, captures a screenshot and uploads the final artifacts.
