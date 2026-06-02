"""Cognitive label vocabularies for FCCS v2 heads.

Extracted as a standalone module so the inference / bridge path does not need
to import the full (training-oriented) ``data.py`` corpus generator.
"""

from __future__ import annotations

INTENT_LABELS = ["factual", "explanatory", "empathetic", "exploratory", "clarifying", "safety"]
TRUTH_LABELS = ["true", "false", "unknown"]
DEDUCTIVE_LABELS = ["entails", "contradicts", "insufficient"]
ABDUCTIVE_LABELS = ["correct", "plausible", "implausible", "unrelated"]
INDUCTIVE_LABELS = ["generalizes", "overgeneralizes", "undergeneralizes"]

__all__ = [
    "INTENT_LABELS",
    "TRUTH_LABELS",
    "DEDUCTIVE_LABELS",
    "ABDUCTIVE_LABELS",
    "INDUCTIVE_LABELS",
]
