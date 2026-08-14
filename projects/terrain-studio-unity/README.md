# Terrain Studio — Unity 6

Main mobile 3D map editor implementation.

## Engine
- Unity 6.3 LTS (6000.3.12f1)
- URP 17.3
- Android / OpenGL ES 3
- ARMv7 compatibility build for the first device test

## Phase 1 implemented
- Runtime 65x65 sculptable mesh terrain
- Raise / lower / smooth / flatten brushes
- Vertex-color ground painting
- Smooth touch orbit camera and pinch zoom
- Lightweight trees and rocks
- Eraser tool
- 12-step terrain undo
- Local JSON save/load
- Directional sun, soft shadows, fog, ambient lighting
- Mobile editor UI generated at runtime

## Controls
- One finger: active editor tool
- Two fingers: orbit + zoom camera
- Camera tool: one-finger orbit

## CI
`.github/workflows/terrain-studio-unity6-android.yml` builds the Android APK using GameCI Unity Builder v5.
The repository requires a GitHub Actions secret named `UNITY_LICENSE` containing a valid Unity `.ulf` license before CI can start the Unity Editor.
