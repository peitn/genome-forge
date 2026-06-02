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

## HuggingFace

- Checkpoint: `peiti/mnemolattice-v01-hex`
- Kaggle dataset: `alenarejdov/phantom-ai-training-pack`
