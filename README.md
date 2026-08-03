# Piano & Violin Academy

An offline-first Flutter Android application for interactive foundational piano and violin learning. It uses Material Design 3, Riverpod, local progress storage, generated royalty-free WAV tones, English/Arabic localization, accessibility settings, exercises, lesson tracking, metronome controls, and permission-safe tuner entry.

## Features

- Playable multi-touch piano keyboard with scrolling, labels, solfège, highlighting, volume, sustain UI, BPM control, and metronome.
- Interactive four-string violin fingerboard, bow direction, reference tones, and tuner permission flow.
- Beginner, intermediate, and advanced lesson catalogs stored as JSON assets.
- Practice scoring, accuracy/timing feedback, local scores, streaks, and achievements.
- English and Arabic with RTL support.
- Light, dark, system, high-contrast, text-scale, vibration, animation, and mirrored-layout settings.
- Offline operation after installation; no account, ads, analytics, or cloud data transfer.

## Project structure

```text
lib/
  main.dart
  app/                 app setup and Riverpod providers
  core/                models, localization, scoring
  services/            audio, metronome, storage, microphone permission
  features/            home, instruments, lessons, practice, progress, settings
  shared/              reusable widgets
assets/
  audio/                programmatically generated WAV tones
  lessons/              lesson JSON
  l10n/                 English and Arabic JSON
android/                Android/Gradle configuration
test/                   unit and widget tests
integration_test/       basic navigation launch test
.github/workflows/      CI APK build and tagged release
```

## Requirements

- Flutter 3.44.0 stable (pinned in CI)
- Dart included with Flutter
- Android SDK and JDK 17

## Run locally

```bash
flutter pub get
flutter run
```

## Quality checks

```bash
flutter analyze
flutter test
flutter test integration_test
```

## Build APKs

```bash
flutter build apk --debug
flutter build apk --release
```

Outputs:

- `build/app/outputs/flutter-apk/app-debug.apk`
- `build/app/outputs/flutter-apk/app-release.apk`

Without production signing configuration, the Android Gradle setup signs release builds with the development debug key so the APK remains installable for testing. This is not suitable for Play Store distribution.

## GitHub Actions

`.github/workflows/build-android.yml` runs on pushes to `main`, pull requests, and manual dispatch. It installs JDK 17 and Flutter 3.44.0, restores caches, runs dependency resolution, analysis and tests, builds debug/release APKs, then uploads:

- `piano-violin-academy-debug-apk`
- `piano-violin-academy-release-apk`

Open the repository's **Actions** tab, choose a successful **Build Android APK** run, then download the artifact from the run's **Artifacts** section.

## Secure production signing

Create a keystore locally and never commit it. Base64-encode it, then add these encrypted repository secrets:

- `ANDROID_KEYSTORE_BASE64`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`

Example encoding on Linux:

```bash
base64 -w 0 upload-keystore.jks > keystore.base64.txt
```

The workflows detect the Base64 secret and generate temporary `android/key.properties` plus the keystore on the runner. Files disappear after the job. If secrets are absent, CI creates an installable development-signed release APK and labels the fallback copy clearly.

## Tagged GitHub Release

```bash
git tag v1.0.0
git push origin v1.0.0
```

`release-android.yml` runs tests, builds the release APK, creates a GitHub Release using the built-in `GITHUB_TOKEN`, and attaches `piano-violin-academy-v1.0.0.apk`.

## Privacy and permissions

Microphone permission is declared because optional pitch detection is exposed in the tuner. It is requested only after the user taps **Enable microphone**. Denial does not affect lessons, instruments, metronome, or reference tones. No microphone data is uploaded.

## Current limitations

- Live microphone pitch estimation is represented by a permission-safe experimental tuner entry; a production DSP pitch detector is not yet implemented.
- Recording/playback buttons and sustain control have UI/service foundations but full session waveform recording, MIDI export, and polyphonic sustain voice management are not complete.
- Generated tones are simple sine-based educational reference samples, not sampled acoustic instruments.
- Lesson educational text is currently English JSON content; all application chrome is English/Arabic, but full bilingual lesson-body translation remains to be added.
- APKs were not built in the repository-generation environment because Flutter SDK was unavailable there. CI is configured to perform the actual build and tests.
