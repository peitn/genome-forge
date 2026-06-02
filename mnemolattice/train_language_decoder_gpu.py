#!/usr/bin/env python3
"""MnemoLattice v0.1 — GPU training script for hex-penta memory decoder."""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

from genomeforge.gpu_language_trainer import (
    ByteTokenizer,
    TinyTorchLMConfig,
    build_compressed_token_stream,
    make_torch_model_class,
    pick_device,
    save_checkpoint,
)


def read_texts(paths: Iterable[str]) -> List[str]:
    texts: List[str] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            for file in sorted(path.rglob("*.txt")):
                texts.append(file.read_text(encoding="utf-8", errors="replace"))
        else:
            texts.append(path.read_text(encoding="utf-8", errors="replace"))
    return [t for t in texts if t]


def build_token_stream(texts: Iterable[str], tokenizer: ByteTokenizer) -> List[int]:
    stream: List[int] = []
    for text in texts:
        stream.extend(tokenizer.encode(text))
        stream.append(tokenizer.eos_id)
    return stream


def make_batch(torch, token_stream, *, batch_size, context, device):
    starts = [random.randint(0, len(token_stream) - context - 1) for _ in range(batch_size)]
    x = [token_stream[s : s + context] for s in starts]
    y = [token_stream[s + 1 : s + context + 1] for s in starts]
    return (
        torch.tensor(x, dtype=torch.long, device=device),
        torch.tensor(y, dtype=torch.long, device=device),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--out", default="checkpoints/mnemolattice_hex.pt")
    ap.add_argument("--vocab", type=int, default=512)
    ap.add_argument("--context", type=int, default=128)
    ap.add_argument("--dim", type=int, default=192)
    ap.add_argument("--hidden", type=int, default=256)
    ap.add_argument("--memory-depth", type=int, default=800)
    ap.add_argument("--memory-geometry", choices=["column", "hex", "fractal_hex"], default="hex")
    ap.add_argument("--hex-cells", type=int, default=7)
    ap.add_argument("--active-depth", type=int, default=64)
    ap.add_argument("--rotation", choices=["off", "phase", "spiral", "spiral_hex"], default="spiral_hex")
    ap.add_argument("--compression", choices=["off", "abstract"], default="abstract")
    ap.add_argument("--ledger", choices=["off", "data", "evolution"], default="evolution")
    ap.add_argument("--ledger-shards", type=int, default=7)
    ap.add_argument("--ledger-consensus", type=int, default=64)
    ap.add_argument("--evolution", choices=["off", "data_blocks"], default="data_blocks")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--log-every", type=int, default=100)
    ap.add_argument("--sample-every", type=int, default=500)
    args = ap.parse_args()

    random.seed(args.seed)
    torch_cls, _, F = __import__("genomeforge.gpu_language_trainer", fromlist=["_require_torch"])._require_torch()
    torch = torch_cls
    torch.manual_seed(args.seed)
    device = pick_device(args.device)

    texts = read_texts(args.data)
    tokenizer = ByteTokenizer(args.vocab)
    token_stream, abstract_compressor = build_compressed_token_stream(
        texts, tokenizer, vocab_size=args.vocab,
        compression=args.compression,
    )
    cfg = TinyTorchLMConfig(
        vocab_size=args.vocab, context_size=args.context,
        embedding_dim=args.dim, hidden_dim=args.hidden,
        memory_depth=args.memory_depth, memory_geometry=args.memory_geometry,
        hex_cells=args.hex_cells, active_depth=args.active_depth,
        rotation=args.rotation, compression=args.compression,
        ledger=args.ledger, ledger_shards=args.ledger_shards,
        ledger_consensus_window=args.ledger_consensus,
        evolution=args.evolution,
    )
    model_cls = make_torch_model_class()
    model = model_cls(cfg).to(device)
    optim = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)

    print(json.dumps({"device": device, "tokens": len(token_stream), "config": cfg.__dict__}, indent=2))

    model.train()
    ema = None
    for step in range(1, args.steps + 1):
        x, y = make_batch(torch, token_stream, batch_size=args.batch_size, context=args.context, device=device)
        logits = model(x)
        loss = F.cross_entropy(logits.reshape(-1, cfg.vocab_size), y.reshape(-1))
        optim.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optim.step()
        val = float(loss.detach().cpu())
        ema = val if ema is None else 0.98 * ema + 0.02 * val
        if step == 1 or step % args.log_every == 0:
            print(f"step={step:06d} loss={val:.4f} ema={ema:.4f} ppl~{math.exp(min(20.0, val)):.2f}")

    out = save_checkpoint(args.out, model, cfg, meta={"steps": args.steps, "device": device})
    print(f"saved_checkpoint={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
