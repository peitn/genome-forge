#!/usr/bin/env python3
"""MnemoLattice Hogwild! — 4-agent sdílené-váhy trénink s virtuálními čipy.

Hogwild! princip:
    shared_model.share_memory()
         ┌────────────────────────────────────────┐
         │  TinyCompactTorchLM (sdílené váhy)      │
         └──┬──────────┬──────────┬──────────────┘
       Agent-0    Agent-1    Agent-2    Agent-3
       (část A)  (část B)  (část C)  (část D)  ← každý čte jiný kus korpusu
         │           │          │          │
       AdamW      AdamW      AdamW      AdamW  ← vlastní optimizer stav
         └──────────────────────────────────────┘
               souběžné zápisy do sdílených vah
               (bez zámků — Hogwild! garantuje konvergenci
                pro dostatečně malé LR a řídké gradienty)

Každý agent může používat jiný virtuální čip:
    --chip blackwell_sim | neuro_unipolar | neuro_bipolar | semi_quantum | cpu

Příklad:
    python mnemolattice/train_hogwild.py \\
        --data data/corpus.txt \\
        --out checkpoints/mnemolattice_hogwild.pt \\
        --n-agents 4 --chip neuro_bipolar \\
        --steps 3000 --device cpu
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from pathlib import Path
from typing import Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if ROOT.exists() and str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# Importuj MnemoLattice runtime z nainstalovaného wheels, ne z repo src/
# (repo src/ obsahuje starší GenomeForge DSL package)
for _p in sys.path[:]:
    if str(SRC) == _p:
        sys.path.remove(_p)

import torch
import torch.multiprocessing as mp
import torch.nn.functional as F

from genomeforge.gpu_language_trainer import (
    TinyTorchLMConfig,
    build_compressed_token_stream,
    ByteTokenizer,
    make_torch_model_class,
    pick_device,
    save_checkpoint,
)
from mnemolattice.virtual_chips import CHIP_NAMES, get_chip


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def read_texts(paths: Iterable[str]) -> List[str]:
    texts: List[str] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for f in sorted(p.rglob("*.txt")):
                texts.append(f.read_text(encoding="utf-8", errors="replace"))
        else:
            texts.append(p.read_text(encoding="utf-8", errors="replace"))
    return [t for t in texts if t.strip()]


def make_batch(token_stream: List[int], *, batch_size: int, context: int, device: str):
    torch_mod = sys.modules.get("torch", torch)
    if len(token_stream) <= context + 1:
        raise ValueError(f"Token stream příliš krátký: {len(token_stream)} ≤ {context+1}")
    starts = [random.randint(0, len(token_stream) - context - 1) for _ in range(batch_size)]
    x = [token_stream[s: s + context] for s in starts]
    y = [token_stream[s + 1: s + context + 1] for s in starts]
    return (
        torch_mod.tensor(x, dtype=torch_mod.long, device=device),
        torch_mod.tensor(y, dtype=torch_mod.long, device=device),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Agent worker (spouští se v každém procesu)
# ─────────────────────────────────────────────────────────────────────────────
def _agent_worker(
    rank: int,
    shared_model,
    token_slice: List[int],
    config: TinyTorchLMConfig,
    args,
    result_queue,
) -> None:
    torch.manual_seed(args.seed + rank * 31)
    random.seed(args.seed + rank * 31)
    device = pick_device(args.device)

    chip = get_chip(args.chip)
    # Každý agent kompiluje/upravuje model nezávisle — ale sdílí parametry
    model = chip.setup(shared_model)
    optimizer = chip.make_optimizer(shared_model.parameters(), lr=args.lr / args.n_agents)

    local_steps = args.steps // args.n_agents
    batch_size = max(1, args.batch_size // args.n_agents)

    ema: Optional[float] = None
    last_log = 0
    t0 = time.time()

    for step in range(1, local_steps + 1):
        x, y = make_batch(token_slice, batch_size=batch_size,
                          context=config.context_size, device=device)

        chip.before_backward(shared_model)

        with chip.forward_context(device):
            logits = shared_model(x)
            loss = F.cross_entropy(
                logits.reshape(-1, config.vocab_size),
                y.reshape(-1),
            )

        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        chip.modify_gradients(shared_model)
        torch.nn.utils.clip_grad_norm_(shared_model.parameters(), 1.0)
        optimizer.step()
        chip.after_step(shared_model)

        val = float(loss.detach().cpu())
        ema = val if ema is None else 0.98 * ema + 0.02 * val

        if step == 1 or step - last_log >= args.log_every:
            ppl = math.exp(min(20.0, val))
            elapsed = time.time() - t0
            print(
                f"[agent{rank}|{args.chip}] "
                f"step={step:05d}/{local_steps} "
                f"loss={val:.4f} ema={ema:.4f} "
                f"ppl~{ppl:.1f} "
                f"t={elapsed:.0f}s"
            )
            last_log = step

    result_queue.put({"rank": rank, "ema_loss": ema, "steps": local_steps})


# ─────────────────────────────────────────────────────────────────────────────
# Hogwild! koordinátor
# ─────────────────────────────────────────────────────────────────────────────
def hogwild_train(
    model,
    token_stream: List[int],
    config: TinyTorchLMConfig,
    args,
) -> dict:
    """Spustí N agentů souběžně se sdílenými vahami (Hogwild!)."""
    model.share_memory()

    n = args.n_agents
    chunk = len(token_stream) // n
    # Překrývající se kusy → každý agent vidí trochu jiný kontext
    slices = []
    for i in range(n):
        start = i * chunk
        end = min(len(token_stream), (i + 2) * chunk)  # mírný overlap
        slices.append(token_stream[start:end])

    ctx = mp.get_context("spawn")
    result_queue = ctx.Queue()

    print(f"\nHogwild! {n} agentů | čip={args.chip} | {args.steps} celkových kroků")
    print(f"Každý agent: {args.steps // n} kroků, batch={args.batch_size // n}\n")

    t_start = time.time()
    processes = []
    for rank in range(n):
        p = ctx.Process(
            target=_agent_worker,
            args=(rank, model, slices[rank], config, args, result_queue),
            daemon=False,
        )
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    results = {}
    while not result_queue.empty():
        r = result_queue.get_nowait()
        results[r["rank"]] = r

    elapsed = time.time() - t_start
    total_steps = sum(r["steps"] for r in results.values())
    avg_ema = sum(r["ema_loss"] for r in results.values()) / max(1, len(results))

    print(f"\n{'='*60}")
    print(f"Hogwild! dokončen za {elapsed:.1f}s")
    print(f"Celkové kroky: {total_steps} ({n} agentů × {args.steps // n})")
    print(f"Průměrná EMA loss: {avg_ema:.4f}  ppl~{math.exp(min(20, avg_ema)):.2f}")
    print(f"{'='*60}\n")

    return {"elapsed": elapsed, "total_steps": total_steps, "avg_ema_loss": avg_ema}


# ─────────────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="MnemoLattice Hogwild! trénink")
    ap.add_argument("--data", nargs="+", required=True, help="Cesta ke korpusu (txt soubory / adresáře)")
    ap.add_argument("--out", default="checkpoints/mnemolattice_hogwild.pt")
    ap.add_argument("--n-agents", type=int, default=4, help="Počet Hogwild! agentů")
    ap.add_argument("--chip", choices=CHIP_NAMES, default="neuro_bipolar",
                    help="Virtuální čip pro akceleraci")
    ap.add_argument("--vocab", type=int, default=512)
    ap.add_argument("--context", type=int, default=128)
    ap.add_argument("--dim", type=int, default=192)
    ap.add_argument("--hidden", type=int, default=256)
    ap.add_argument("--memory-depth", type=int, default=800)
    ap.add_argument("--memory-geometry", choices=["column", "hex", "fractal_hex"], default="hex")
    ap.add_argument("--active-depth", type=int, default=64)
    ap.add_argument("--rotation", default="spiral_hex")
    ap.add_argument("--compression", default="abstract")
    ap.add_argument("--ledger", default="evolution")
    ap.add_argument("--ledger-shards", type=int, default=7)
    ap.add_argument("--ledger-consensus", type=int, default=64)
    ap.add_argument("--evolution", default="data_blocks")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--steps", type=int, default=6000, help="Celkový počet kroků (rozděleno mezi agenty)")
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--log-every", type=int, default=100)
    args = ap.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = pick_device(args.device)

    print(f"Zařízení: {device} | agenti: {args.n_agents} | čip: {args.chip}")

    texts = read_texts(args.data)
    print(f"Načteno {len(texts)} textů ({sum(len(t) for t in texts):,} znaků)")

    tokenizer = ByteTokenizer(args.vocab)
    token_stream, abstract_compressor = build_compressed_token_stream(
        texts, tokenizer,
        vocab_size=args.vocab,
        compression=args.compression,
    )
    print(f"Token stream: {len(token_stream):,} tokenů")

    cfg = TinyTorchLMConfig(
        vocab_size=args.vocab, context_size=args.context,
        embedding_dim=args.dim, hidden_dim=args.hidden,
        memory_depth=args.memory_depth, memory_geometry=args.memory_geometry,
        hex_cells=7, active_depth=args.active_depth,
        rotation=args.rotation, compression=args.compression,
        ledger=args.ledger, ledger_shards=args.ledger_shards,
        ledger_consensus_window=args.ledger_consensus,
        evolution=args.evolution,
    )

    model_cls = make_torch_model_class()
    model = model_cls(cfg).to("cpu")  # Hogwild! vyžaduje CPU shared memory
    p_count = sum(p.numel() for p in model.parameters())
    print(f"Model: {p_count/1e6:.2f}M parametrů | {p_count*4/1024/1024:.1f} MB (FP32)")
    print(json.dumps({"config": cfg.__dict__}, indent=2))

    results = hogwild_train(model, token_stream, cfg, args)

    meta = {
        "hogwild_agents": args.n_agents,
        "virtual_chip": args.chip,
        "device": device,
        "steps": args.steps,
        "avg_ema_loss": results["avg_ema_loss"],
        "elapsed_s": results["elapsed"],
        "abstract_compressor": abstract_compressor,
    }
    out_path = save_checkpoint(args.out, model, cfg, meta=meta)
    print(f"Checkpoint uložen: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
