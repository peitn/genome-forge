# Feature map

## Implemented in Flutter shell

- Responsive navigation: Dashboard, Studio, Games, Assets, Build.
- Dashboard metrics: water, heat, fracture risk, AI signal.
- Event log with simulated runtime events.
- Procedural mini world viewport.
- Procedural isometric 3D studio viewport.
- Editor controls: tool chips, material chips, brush size slider, command button.
- Four prepared game templates.
- Animation showcase based on Flutter `CustomPainter`.
- Audio hook via built-in system click.
- Generated placeholder WAV assets.
- Android signing template files.

## Not implemented yet

- Real 3D mesh engine.
- Real physics loop from Python.
- Real file save/load from the original Python world state.
- Real audio playback of WAV assets.
- Multiplayer/networking.
- GPU renderer / shader pipeline.

## Recommended next step

Build a small local backend around the Python engine and let Flutter call it with HTTP or WebSocket. That is much cleaner than trying to rewrite the whole simulation engine into Dart immediately.
