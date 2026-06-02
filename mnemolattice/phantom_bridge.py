#!/usr/bin/env python3
"""PhantomBridge — couple FCCS (cognition) to MnemoLattice (memory/generation).

Architecture (Option B: memory injection / cognitive conditioning)
==================================================================

    text ──► FCCS v2  ──► cognitive signal ──► PhantomBridge ──► MnemoLattice
             (classify)    intent / truth /      maps signal       (generate,
                            reasoning / emotion   into the 5        conditioned
                            / confidence + a      P/U/Z/B/eta       on cognition)
                            64-dim adapter        memory channels
                            latent                + a logit bias

Why this design (and not a shared encoder / multitask retrain):

* FCCS operates on **sentence-level** embeddings (384-dim sentence-transformer);
  MnemoLattice operates on **byte-level** tokens. They live at different
  granularities, so a single shared encoder would be awkward and force a full
  retrain that merges incompatible tokenizations.
* This bridge keeps **both already-trained models intact** and adds a thin,
  deterministic coupling layer. FCCS becomes a *cognitive filter* that writes
  its reasoning state into MnemoLattice's memory channels and nudges the
  decoder's logits — without hijacking generation.

The bridge mirrors the stable contract of ``genomeforge.cogcore_bridge``
(``modulate_logits(logits, *, prompt_text, tokens)``) so it plugs directly into
the decoder via ``attach_logits_backend`` / ``TorchCheckpointBackend``.

The five MnemoLattice memory channels are P / U / Z / B / eta:
    P   (presence/energy)   ← model confidence
    U   (uncertainty)       ← mean reasoning entropy (1 − confidence proxy)
    Z   (truth axis)        ← P(true) − P(false)
    B   (affect/intent bias)← emotion valence, lifted by empathetic intent
    eta (consolidation)     ← arousal × confidence (how strongly to commit)
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# Put the repo root on the path so the vendored `fccs_v2` package imports.
# The MnemoLattice runtime (`genomeforge.gpu_language_trainer`,
# `genomeforge.language_decoder`) is provided by the installed
# `genomeforge>=0.6.7` wheel, so we deliberately do NOT prepend `src/`
# (the older GenomeForge DSL package) ahead of it.
ROOT = Path(__file__).resolve().parents[1]
if ROOT.exists() and str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# --------------------------------------------------------------------------- #
# Cognitive signal                                                            #
# --------------------------------------------------------------------------- #
@dataclass
class PhantomCognitiveSignal:
    """Compact, stable interchange object produced by FCCS for MnemoLattice."""

    intent: str
    truth: str
    deductive: str
    abductive: str
    inductive: str
    valence: float
    arousal: float
    confidence: float
    # Five-channel memory write vector P / U / Z / B / eta, each in a sane range.
    memory_channels: Dict[str, float] = field(default_factory=dict)
    # Scalar logit bias applied uniformly to the decoder distribution.
    logit_bias: float = 0.0
    # Planner hint from the FCCS bio-core bridge (e.g. "slow_down_ground_check_risk").
    planner: str = ""
    # Raw 64-dim adapter latent (kept for downstream / analysis use).
    adapter: List[float] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "truth": self.truth,
            "deductive": self.deductive,
            "abductive": self.abductive,
            "inductive": self.inductive,
            "valence": self.valence,
            "arousal": self.arousal,
            "confidence": self.confidence,
            "memory_channels": self.memory_channels,
            "logit_bias": self.logit_bias,
            "planner": self.planner,
        }


# --------------------------------------------------------------------------- #
# Bridge                                                                       #
# --------------------------------------------------------------------------- #
class PhantomBridge:
    """Turn FCCS cognitive predictions into MnemoLattice conditioning.

    Construct via :meth:`from_bundle` with a trained FCCS bundle directory
    (``config.json`` + ``model.pt``). The bridge can then:

    * :meth:`summarize` — classify text into a :class:`PhantomCognitiveSignal`.
    * :meth:`modulate_logits` — bias a decoder's logits using that signal
      (same contract as ``CogCoreBridge.modulate_logits``).
    """

    def __init__(self, *, bundle: Any, bias_gain: float = 0.06):
        self._bundle = bundle
        self.bias_gain = float(bias_gain)
        self._cache: Dict[str, PhantomCognitiveSignal] = {}

    # ---- construction ---------------------------------------------------- #
    @classmethod
    def from_bundle(cls, fccs_bundle_dir: str | Path, *, bias_gain: float = 0.06) -> "PhantomBridge":
        """Load a trained FCCS bundle (config.json + model.pt)."""
        try:
            from fccs_v2.infer import load_bundle  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on environment
            raise ImportError(
                "PhantomBridge.from_bundle() needs the vendored `fccs_v2` package "
                "on sys.path (it ships alongside this module in the repo root)."
            ) from exc
        bundle = load_bundle(Path(fccs_bundle_dir))
        return cls(bundle=bundle, bias_gain=bias_gain)

    # ---- cognition ------------------------------------------------------- #
    def summarize(self, text: str) -> PhantomCognitiveSignal:
        if text in self._cache:
            return self._cache[text]
        from fccs_v2.infer import predict_text  # type: ignore

        pred = predict_text(self._bundle, text)
        signal = self._prediction_to_signal(pred)
        self._cache[text] = signal
        return signal

    @staticmethod
    def _truth_axis(truth_probs: Sequence[float]) -> float:
        # TRUTH_LABELS = ["true", "false", "unknown"]  ->  P(true) - P(false)
        if len(truth_probs) < 2:
            return 0.0
        return float(truth_probs[0] - truth_probs[1])

    def _prediction_to_signal(self, pred: Dict[str, Any]) -> PhantomCognitiveSignal:
        conf = float(pred["confidence"]["value"])
        valence = float(pred["emotion"]["valence"])
        arousal = float(pred["emotion"]["arousal"])
        truth_axis = self._truth_axis(pred["truth"]["probs"])

        intent_probs = pred["intent"]["probs"]
        # INTENT_LABELS = [factual, explanatory, empathetic, exploratory, clarifying, safety]
        empathetic_p = intent_probs[2] if len(intent_probs) > 2 else 0.0
        safety_p = intent_probs[5] if len(intent_probs) > 5 else 0.0

        # --- map cognition into the 5 P/U/Z/B/eta memory channels --- #
        channels = {
            "P": round(conf, 4),                                   # presence/energy
            "U": round(1.0 - conf, 4),                             # uncertainty
            "Z": round(truth_axis, 4),                             # truth axis
            "B": round(max(-1.0, min(1.0, valence + 0.4 * empathetic_p)), 4),  # affect/intent
            "eta": round(max(0.0, min(1.0, arousal * conf)), 4),   # consolidation strength
        }

        # --- scalar logit bias --- #
        # Confident, truthful prompts gently sharpen the decoder; safety / low
        # confidence pulls it back. Kept small so cognition guides, not hijacks.
        bias = self.bias_gain * (
            0.6 * (conf - 0.5)
            + 0.3 * truth_axis
            - 0.5 * safety_p
        )

        planner = ""
        bio = pred.get("bio_core")
        if isinstance(bio, dict):
            planner = str(bio.get("planner", ""))

        return PhantomCognitiveSignal(
            intent=pred["intent"]["label"],
            truth=pred["truth"]["label"],
            deductive=pred["deductive"]["label"],
            abductive=pred["abductive"]["label"],
            inductive=pred["inductive"]["label"],
            valence=valence,
            arousal=arousal,
            confidence=conf,
            memory_channels=channels,
            logit_bias=round(float(bias), 6),
            planner=planner,
            adapter=list(pred.get("adapter", [])),
        )

    # ---- decoder conditioning (CogCoreBridge-compatible contract) -------- #
    def modulate_logits(
        self,
        logits: Sequence[float],
        *,
        prompt_text: str,
        tokens: Sequence[int],
    ) -> List[float]:
        """Bias decoder logits with the FCCS cognitive signal for ``prompt_text``."""
        signal = self.summarize(prompt_text)
        out = [float(x) + signal.logit_bias for x in logits]
        if not out:
            return out
        # Tiny deterministic, signal-conditioned ripple. The phase is driven by
        # the truth/consolidation channels so different cognitive states produce
        # different — but reproducible — nudges. Deliberately small.
        eta = signal.memory_channels.get("eta", 0.0)
        z = signal.memory_channels.get("Z", 0.0)
        phase = int(abs(z + eta) * 1_000_003) + len(tokens)
        ripple = 0.02 + 0.04 * eta
        for i in range(len(out)):
            if ((i + phase) % 97) == 0:
                out[i] += ripple
        return out


# --------------------------------------------------------------------------- #
# Conditioned inference backend                                               #
# --------------------------------------------------------------------------- #
class PhantomConditionedBackend:
    """Wrap a MnemoLattice logits backend so every step is FCCS-conditioned.

    Exposes the same ``logits(tokens, *, prompt_text=None)`` and
    ``generate(...)`` surface as ``TorchCheckpointBackend``, so it can be
    attached to a ``CompactLanguageDecoder`` via ``attach_logits_backend``.
    """

    def __init__(self, inner: Any, bridge: PhantomBridge):
        self.inner = inner
        self.bridge = bridge

    def logits(self, tokens: Sequence[int], *, prompt_text: Optional[str] = None) -> List[float]:
        raw = self.inner.logits(tokens, prompt_text=prompt_text)
        if not prompt_text:
            return raw
        return self.bridge.modulate_logits(raw, prompt_text=prompt_text, tokens=tokens)

    def generate(self, tokenizer: Any, prompt: str, *, max_tokens: int = 64, temperature: float = 1.0, top_k: int = 40) -> str:
        import torch  # local import; only needed when generating

        tokens = tokenizer.encode(prompt) or [tokenizer.bos_id]
        for _ in range(max_tokens):
            vals = self.logits(tokens, prompt_text=prompt)
            logits = torch.tensor(vals, dtype=torch.float32)
            if top_k > 0 and top_k < logits.numel():
                topv, topi = torch.topk(logits, k=top_k)
                probs = torch.softmax(topv / max(temperature, 1e-6), dim=-1)
                next_id = int(topi[torch.multinomial(probs, 1).item()].item())
            else:
                probs = torch.softmax(logits / max(temperature, 1e-6), dim=-1)
                next_id = int(torch.multinomial(probs, 1).item())
            tokens.append(next_id)
        return tokenizer.decode(tokens)


def attach_phantom_bridge(
    decoder: Any,
    checkpoint_path: str | Path,
    fccs_bundle_dir: str | Path,
    *,
    device: str = "auto",
    bias_gain: float = 0.06,
) -> Any:
    """Attach a GPU-trained MnemoLattice checkpoint, FCCS-conditioned.

    Returns the decoder with a :class:`PhantomConditionedBackend` attached.
    """
    from genomeforge.gpu_language_trainer import TorchCheckpointBackend  # type: ignore

    inner = TorchCheckpointBackend(checkpoint_path, device=device)
    bridge = PhantomBridge.from_bundle(fccs_bundle_dir, bias_gain=bias_gain)
    backend = PhantomConditionedBackend(inner, bridge)
    if getattr(inner, "abstract_compressor_snapshot", None) and hasattr(decoder, "load_abstract_tokens"):
        decoder.load_abstract_tokens(inner.abstract_compressor_snapshot)
    decoder.attach_logits_backend(backend)
    return decoder
