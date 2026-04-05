# Examples

This directory currently contains four example forms:

- `minimal.genome` — the simplest direct example used by the smallest tests
- `connected.genome` — a multi-module routing example
- `baseline_restored.genome` — reconstructed plaintext form of the baseline example
- `baseline.genome.bigcontainer/` — Big Container representation of the original baseline file

## Restore Big Container files

You can restore every `*.bigcontainer` bundle in the repository with:

```bash
python import_all_bigcontainers.py --repo-root .
```

To overwrite already restored files:

```bash
python import_all_bigcontainers.py --repo-root . --overwrite
```
