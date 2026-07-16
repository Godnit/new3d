# City Quest 3D Legacy — Android 8.1 and Web

A compact third-person 3D city mission game rebuilt specifically for older Android phones such as the LG LM-X212TA running Android 8.1.

## Compatibility design

- Godot 4.6.3 GL Compatibility renderer; Vulkan is not required.
- Forced landscape orientation at project and runtime levels.
- 960×540 internal resolution, 30 FPS cap, disabled MSAA and real-time shadows.
- A smaller city and staged loading to avoid long black screens and Android “not responding” warnings.
- Separate Android 8.1 emulator build used for automated black-screen and orientation checks.
- Browser/Web preview exported from the same project before APK installation.

## Game content

- Third-person movement, sprinting, jumping and camera rotation.
- Ready-made Kenney city buildings and vehicle models rather than primitive placeholder shapes.
- KayKit Adventurers characters: rigged, animated, mobile-optimized low-poly models with lightweight TABS-inspired wobble and squash motion.
- Three pursuing enemies, melee combat, health, collectibles and four linked mission stages.
- Enter, drive and exit a car.
- Touch controls, pause, restart, win and lose states.
- Offline after installation.

## Automated acceptance test

The CI downloads the licensed CC0 assets, imports them in Godot, runs an OpenGL gameplay smoke test, renders a desktop preview, exports the Android APK and Web preview, installs the emulator APK on Android 8.1 (API 27), launches the game, captures menu and gameplay screenshots, and rejects the build if either screenshot is portrait, black or visually blank.
