# Audio assets

This folder contains tiny generated WAV placeholders:

- `click.wav` — short UI click
- `bridge_ping.wav` — short bridge/sensor ping

The app currently uses Flutter's built-in `SystemSound.play(SystemSoundType.click)` to avoid external dependencies. To play these WAV files directly, add a playback package such as `audioplayers` later and wire the buttons in `AssetsScreen`.
