"""Unit tests for the PhantomBridge cognition→memory mapping.

These tests exercise the deterministic mapping layer without loading any torch
model: a synthetic FCCS prediction dict is fed straight into the bridge.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mnemolattice.phantom_bridge import PhantomBridge, PhantomCognitiveSignal


def _fake_prediction(*, confidence, valence, arousal, truth_probs, intent_probs,
                     intent="factual", truth="true"):
    return {
        "text": "x",
        "adapter": [0.0] * 64,
        "intent": {"label": intent, "probs": intent_probs},
        "truth": {"label": truth, "probs": truth_probs},
        "deductive": {"label": "entails", "probs": [0.8, 0.1, 0.1]},
        "abductive": {"label": "correct", "probs": [0.7, 0.1, 0.1, 0.1]},
        "inductive": {"label": "generalizes", "probs": [0.8, 0.1, 0.1]},
        "emotion": {"valence": valence, "arousal": arousal},
        "confidence": {"value": confidence},
        "bio_core": {"planner": "structured_answer_with_confidence_note"},
    }


def _bridge():
    # bundle is unused by _prediction_to_signal, so a bare bridge is fine.
    return PhantomBridge(bundle=None)


def test_signal_is_returned():
    pred = _fake_prediction(
        confidence=0.9, valence=0.2, arousal=0.3,
        truth_probs=[0.9, 0.05, 0.05],
        intent_probs=[0.9, 0.02, 0.02, 0.02, 0.02, 0.02],
    )
    sig = _bridge()._prediction_to_signal(pred)
    assert isinstance(sig, PhantomCognitiveSignal)
    assert sig.confidence == 0.9
    assert set(sig.memory_channels) == {"P", "U", "Z", "B", "eta"}


def test_truth_axis_positive_when_true_dominates():
    pred = _fake_prediction(
        confidence=0.8, valence=0.0, arousal=0.1,
        truth_probs=[0.95, 0.02, 0.03],
        intent_probs=[0.9, 0.02, 0.02, 0.02, 0.02, 0.02],
    )
    sig = _bridge()._prediction_to_signal(pred)
    assert sig.memory_channels["Z"] > 0.5  # P(true) - P(false)
    assert sig.memory_channels["P"] == 0.8
    assert abs(sig.memory_channels["U"] - 0.2) < 1e-6


def test_truth_axis_negative_when_false_dominates():
    pred = _fake_prediction(
        confidence=0.4, valence=0.0, arousal=0.1, truth="false",
        truth_probs=[0.05, 0.9, 0.05],
        intent_probs=[0.9, 0.02, 0.02, 0.02, 0.02, 0.02],
    )
    sig = _bridge()._prediction_to_signal(pred)
    assert sig.memory_channels["Z"] < -0.5


def test_safety_intent_lowers_logit_bias():
    high_safety = _fake_prediction(
        confidence=0.5, valence=0.0, arousal=0.2,
        truth_probs=[0.5, 0.3, 0.2],
        intent_probs=[0.1, 0.1, 0.1, 0.1, 0.1, 0.5],  # safety dominant
    )
    low_safety = _fake_prediction(
        confidence=0.5, valence=0.0, arousal=0.2,
        truth_probs=[0.5, 0.3, 0.2],
        intent_probs=[0.5, 0.1, 0.1, 0.1, 0.1, 0.1],  # factual dominant
    )
    b = _bridge()
    assert b._prediction_to_signal(high_safety).logit_bias < b._prediction_to_signal(low_safety).logit_bias


def test_eta_tracks_arousal_and_confidence():
    calm = _fake_prediction(
        confidence=0.9, valence=0.0, arousal=0.0,
        truth_probs=[0.8, 0.1, 0.1],
        intent_probs=[0.9, 0.02, 0.02, 0.02, 0.02, 0.02],
    )
    aroused = _fake_prediction(
        confidence=0.9, valence=0.0, arousal=0.9,
        truth_probs=[0.8, 0.1, 0.1],
        intent_probs=[0.9, 0.02, 0.02, 0.02, 0.02, 0.02],
    )
    b = _bridge()
    assert b._prediction_to_signal(calm).memory_channels["eta"] == 0.0
    assert b._prediction_to_signal(aroused).memory_channels["eta"] > 0.5


def test_modulate_logits_preserves_length_and_applies_bias():
    pred = _fake_prediction(
        confidence=0.9, valence=0.0, arousal=0.2,
        truth_probs=[0.9, 0.05, 0.05],
        intent_probs=[0.9, 0.02, 0.02, 0.02, 0.02, 0.02],
    )
    b = _bridge()
    sig = b._prediction_to_signal(pred)
    b._cache["hello"] = sig  # bypass model
    base = [0.0] * 200
    out = b.modulate_logits(base, prompt_text="hello", tokens=[1, 2, 3])
    assert len(out) == len(base)
    # Every position gets at least the uniform logit bias.
    assert all(v >= sig.logit_bias - 1e-9 for v in out)
    # Determinism: same inputs → same outputs.
    assert out == b.modulate_logits(base, prompt_text="hello", tokens=[1, 2, 3])
