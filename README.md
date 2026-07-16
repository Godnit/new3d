# City Quest 3D — Android

A complete small 3D city mission game built with Godot 4.6.3 and exported as a real Android APK.

## Gameplay

- Third-person movement, sprint and jump
- Touch controls designed for landscape phones
- Imported Kenney 3D buildings and cars, plus an imported Khronos glTF character
- Enemy pursuit and melee combat
- Collectibles, health and four-stage mission flow
- Enter, drive and exit a car
- Pause, restart, win and lose states
- Offline after installation

## Android build

The APK uses Godot's mobile renderer with an OpenGL fallback. The automated build downloads the licensed ready-made 3D models, imports them, runs a scene smoke test, exports and signs the APK, validates its archive, and packages the full editable source.
