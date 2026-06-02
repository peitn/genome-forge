# FCCS v2.2 — Kognitivní klasifikátor

Multi-head PyTorch model pro klasifikaci textu do kognitivních dimenzí.

## Enkodéry

- `hash` — deterministický hash-projection (bez závislostí, rychlý)
- `sentence-transformer` — `paraphrase-multilingual-MiniLM-L12-v2` (lepší sémantika)

## Výstup

| Hlava | Třídy |
|-------|-------|
| intent | factual / explanatory / empathetic / exploratory / clarifying / safety |
| truth | true / false / unknown |
| deductive | entails / contradicts / insufficient |
| abductive | correct / plausible / implausible / unrelated |
| inductive | generalizes / overgeneralizes / undergeneralizes |
| emotion | valence + arousal (regrese) |
| confidence | meta-jistota (regrese) |

## HuggingFace Space

https://huggingface.co/spaces/peiti/fccs-v22-hebbian-web
