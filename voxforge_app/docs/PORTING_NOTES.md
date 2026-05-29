# Porting notes

## Safe architecture

Use Flutter for:

- UI
- editing panels
- mobile shell
- game menus
- asset browser
- input controls
- preview visualizations

Keep Python or native code for:

- heavy voxel simulation
- fluid/thermal/fracture steps
- AI agents
- save/load conversion
- meshing and world snapshots

## Bridge options

1. HTTP backend: easiest to debug.
2. WebSocket backend: best for live tick streaming.
3. Platform channel: useful for Android/iOS native modules.
4. FFI/native library: fastest, but more work.

## Data flow

```text
Flutter button -> command DTO -> backend sim tick -> world snapshot -> Flutter viewport
```

Start with JSON snapshots. Optimize later only if the data becomes too large.
