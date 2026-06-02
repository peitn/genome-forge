from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import torch

from .config import FCCSV2Config
from .labels import (
    ABDUCTIVE_LABELS,
    DEDUCTIVE_LABELS,
    INDUCTIVE_LABELS,
    INTENT_LABELS,
    TRUTH_LABELS,
)
from .encoders import AutoTextEncoder
from .model import FCCSV2Model
from .semantic_bridge import semantic_bridge


def _softmax_list(x: torch.Tensor) -> List[float]:
    return [round(float(v), 4) for v in torch.softmax(x, dim=-1).tolist()]


def load_bundle(bundle_dir: str | Path) -> Dict[str, object]:
    bundle_dir = Path(bundle_dir)
    config = FCCSV2Config.from_json(bundle_dir / "config.json")
    encoder = AutoTextEncoder(
        mode=config.encoder.mode,
        embedding_dim=config.encoder.embedding_dim,
        hash_buckets=config.encoder.hash_buckets,
        seed=config.encoder.seed,
        sentence_model_name=config.encoder.sentence_model_name,
    )
    model = FCCSV2Model(
        input_dim=config.encoder.embedding_dim,
        hidden_dim=config.train.hidden_dim,
        adapter_dim=config.train.adapter_dim,
    )
    state = torch.load(bundle_dir / "model.pt", map_location="cpu")
    model.load_state_dict(state)
    model.eval()
    return {"config": config, "encoder": encoder, "model": model, "bundle_dir": str(bundle_dir)}


@torch.no_grad()
def predict_text(bundle_or_text, text_or_bundle) -> Dict[str, object]:
    """Flexible signature — accepts either (bundle, text) or (text, bundle)."""
    if isinstance(bundle_or_text, dict):
        bundle, text = bundle_or_text, text_or_bundle
    else:
        text, bundle = bundle_or_text, text_or_bundle
    encoder = bundle["encoder"]
    model = bundle["model"]
    x = encoder.encode([text]).float()
    out = model(x)

    intent_logits = out["intent"][0]
    truth_logits = out["truth"][0]
    deductive_logits = out["deductive"][0]
    abductive_logits = out["abductive"][0]
    inductive_logits = out["inductive"][0]
    emotion_raw = out["emotion"][0]
    confidence_raw = out["confidence"][0]

    prediction = {
        "text": text,
        # Raw adapter latent (64-dim by default) — used by PhantomBridge to write
        # FCCS reasoning state into MnemoLattice's memory channels.
        "adapter": [round(float(v), 6) for v in out["adapter"][0].tolist()],
        "intent": {
            "label": INTENT_LABELS[int(torch.argmax(intent_logits).item())],
            "probs": _softmax_list(intent_logits),
        },
        "truth": {
            "label": TRUTH_LABELS[int(torch.argmax(truth_logits).item())],
            "probs": _softmax_list(truth_logits),
        },
        "deductive": {
            "label": DEDUCTIVE_LABELS[int(torch.argmax(deductive_logits).item())],
            "probs": _softmax_list(deductive_logits),
        },
        "abductive": {
            "label": ABDUCTIVE_LABELS[int(torch.argmax(abductive_logits).item())],
            "probs": _softmax_list(abductive_logits),
        },
        "inductive": {
            "label": INDUCTIVE_LABELS[int(torch.argmax(inductive_logits).item())],
            "probs": _softmax_list(inductive_logits),
        },
        "emotion": {
            "valence": round(float(torch.clamp(emotion_raw[0], -1.0, 1.0).item()), 4),
            "arousal": round(float(torch.clamp(emotion_raw[1], 0.0, 1.0).item()), 4),
        },
        "confidence": {
            # Model už vrací hodnotu ~v [0,1], jen ořežeme.
            "value": round(float(torch.clamp(confidence_raw[0], 0.0, 1.0).item()), 4),
        },
    }
    prediction["bio_core"] = semantic_bridge(prediction)
    return prediction


@torch.no_grad()
def predict_json(text: str, bundle_dir: str | Path) -> str:
    bundle = load_bundle(bundle_dir)
    return json.dumps(predict_text(bundle, text), ensure_ascii=False, indent=2)
