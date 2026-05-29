# VoxForge / Noctilith Flutter Superpack

Portable Flutter starter app for the uploaded `voxforge_noctilith_merged.zip` prototype.

This is **not** a full 1:1 rewrite of the Python simulation engine into Dart. It is a ready Flutter shell / mobile control-studio layer that you can copy into a real Flutter SDK project and then connect to the Python engine through HTTP/WebSocket, platform channels, FFI, or a native backend.

## What was verified

The original Python package was unpacked and tested:

```bash
cd voxforge_noctilith_merged
python -m pytest -q
```

Result:

```text
51 passed, 1 warning
```

Flutter SDK is not installed in this sandbox, so `flutter analyze`, `flutter test`, and Android builds must be run on your machine.

## What this app contains

- Dashboard for world/simulation status.
- 3D editing studio shell with procedural isometric viewport.
- Builder tools: brush, erase, material paint, fluid source, heat injector, fracture probe, agent spawner, prefab stamp.
- Prepared game templates: Sandbox Builder, Fluid Puzzle, Arena Runner, Colony Agents.
- Graphics and animation kit using `CustomPainter` and `AnimationController`.
- Audio placeholders: generated WAV files plus built-in `SystemSound` click hook.
- Android release signing templates.
- Original source ZIP included in `source_input/` for one-file transfer.

## How to use

Create a clean Flutter project:

```bash
flutter create voxforge_noctilith_studio
cd voxforge_noctilith_studio
```

Copy the contents of this superpack into the generated project, replacing `lib/main.dart` and `pubspec.yaml`.

Then run:

```bash
flutter pub get
flutter analyze
flutter test
flutter run
```

## Android signing

This package contains signing templates only. It intentionally does **not** include a real private production key.

Never commit these private files:

```text
android/key.properties
*.jks
*.keystore
```

Generate your local upload key:

```bash
bash tool/generate_upload_keystore.sh
```

Then copy and edit:

```bash
cp android/key.properties.example android/key.properties
```

Open `android/app/build.gradle.kts.signing-fragment` and paste the marked sections into the generated Flutter Android Gradle file.

Build release bundle:

```bash
flutter build appbundle --release
```

## Future bridge idea

Keep the Python engine as the simulation backend and expose something like:

```text
POST /world/create
POST /sim/tick
POST /fluid/add
POST /thermal/spike
GET  /world/snapshot
```

Then replace the local mock state in `lib/main.dart` with real backend calls.
