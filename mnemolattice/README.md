# MnemoLattice v0.1 — Paměťový systém

Kompaktní GPU-trénovatelný language decoder s hex-penta paměťovou mřížkou.
Slouží jako paměťový backend pro FCCS kognitivní klasifikátor.

## Architektura

```
bytes/tokens → abstract compression → embeddings
    → adjacent pair interaction
    → hex-penta lattice (memory_depth=800, active_depth=64)
    → spiral_hex rotation + data-ledger evolution
    → tied logits → next token
```

## Trénink na Kaggle GPU

```bash
# Dataset: alenarejdov/phantom-ai-training-pack
python train_language_decoder_gpu.py \
  --data /kaggle/input/phantom-ai-training-pack/data/tiny_corpus.txt \
  --out /kaggle/working/checkpoints/mnemolattice_hex.pt \
  --vocab 512 --context 128 --dim 192 --hidden 256 \
  --memory-geometry hex --hex-cells 7 \
  --memory-depth 800 --active-depth 64 \
  --rotation spiral_hex --compression abstract \
  --ledger evolution --evolution data_blocks \
  --steps 3000 --device auto
```

## Integrace s FCCS

```python
from genomeforge.language_decoder import CompactLanguageDecoder, LanguageDecoderConfig
from genomeforge.gpu_language_trainer import attach_torch_checkpoint
from genomeforge.cogcore_bridge import CogCoreBridge

# CogCore bridge napojený na FCCS embeddingy
bridge = CogCoreBridge.build_default(fit_texts=["example text"])
decoder = CompactLanguageDecoder(
    LanguageDecoderConfig(vocab_size=512, emit="text"),
    cogcore_bridge=bridge
)
attach_torch_checkpoint(decoder, "checkpoints/mnemolattice_hex.pt")

# Generate s paměťovým kontextem
result = decoder.generate("Phantom AI:", max_tokens=128)
print(result.text)
```

## PhantomBridge — propojení FCCS ↔ MnemoLattice

`phantom_bridge.py` spojuje **FCCS** (kognitivní klasifikátor) s **MnemoLattice**
(paměť/generace) metodou *memory injection / cognitive conditioning* (Option B).

```
text → FCCS → kognitivní signál → PhantomBridge → MnemoLattice
       (klasifikace)  intent / truth / reasoning /   mapuje signál    (generace
                      emotion / confidence + 64-dim    do 5 kanálů      podmíněná
                      adapter latent                   P/U/Z/B/eta      kognicí)
                                                       + logit bias
```

**Proč tento návrh** (a ne sdílený encoder / multitask retrain): FCCS pracuje na
úrovni **vět** (384-dim sentence-transformer), MnemoLattice na úrovni **bajtů**.
Liší se granularita, takže jeden sdílený encoder by byl nepřirozený a vynutil by
plný retrain. Bridge nechává **oba natrénované modely beze změny** a přidává
tenkou, deterministickou propojovací vrstvu. FCCS funguje jako *kognitivní filtr*,
který zapisuje svůj stav uvažování do paměťových kanálů a jemně posouvá logity
dekodéru (bez „únosu“ generace).

Pět paměťových kanálů **P / U / Z / B / eta**:

| kanál | význam | zdroj z FCCS |
|-------|--------|--------------|
| P   | presence / energie     | confidence |
| U   | nejistota              | 1 − confidence |
| Z   | osa pravdivosti        | P(true) − P(false) |
| B   | afekt / intent bias    | emotion valence (+ empathetic intent) |
| eta | síla konsolidace       | arousal × confidence |

Bridge dodržuje stabilní kontrakt `genomeforge.cogcore_bridge`
(`modulate_logits(logits, *, prompt_text, tokens)`), takže se napojí přes
`attach_logits_backend`.

```python
from mnemolattice.phantom_bridge import attach_phantom_bridge
from genomeforge.language_decoder import CompactLanguageDecoder, LanguageDecoderConfig

decoder = CompactLanguageDecoder(LanguageDecoderConfig(vocab_size=512, emit="text"))
attach_phantom_bridge(
    decoder,
    checkpoint_path="checkpoints/mnemolattice_hex.pt",
    fccs_bundle_dir="artifacts/base",   # FCCS config.json + model.pt
)
result = decoder.generate("Phantom AI:", max_tokens=128)
print(result.text)
```

Demo (porovná baseline vs. FCCS-podmíněnou generaci):

```bash
python mnemolattice/phantom_bridge_demo.py \
  --fccs-bundle artifacts/base \
  --checkpoint  checkpoints/mnemolattice_hex.pt
```

> Vyžaduje nainstalovaný `genomeforge>=0.6.7` (MnemoLattice runtime) a vendorovaný
> balík `fccs_v2/` z kořene repozitáře. Jednotkové testy mapování:
> `pytest tests/test_phantom_bridge.py`.

## HuggingFace

- Checkpoint: `peiti/mnemolattice-v01-hex`
- Kaggle dataset: `alenarejdov/phantom-ai-training-pack`
