# AR Cube (real ARCore)

A minimal Android AR test app built with ARCore + SceneView/Filament.

## What it does
- Opens the real rear camera.
- Detects real horizontal/vertical surfaces.
- Shows a placement reticle.
- Tap a detected surface to place a 3D cube.
- The cube is attached to an ARCore Anchor so it stays in the room as you move.
- Clear all cubes and try again.
- If the device is not ARCore-certified, the app shows a clear compatibility message instead of crashing.

## Build
GitHub Actions builds the project on Ubuntu with Java 21 and Gradle 8.14.5.

Local build:
```bash
cd ar-cube-app
gradle :app:assembleDebug
```

APK output:
`app/build/outputs/apk/debug/app-debug.apk`
