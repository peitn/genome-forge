from __future__ import annotations

from typing import Dict

import torch
from torch import nn


class FCCSV21Model(nn.Module):
    """
    FCCS v2.1 — oddělené kognitivní kanály pro různé typy uvažování.

    Klasifikační úlohy (každá má vlastní softmax head):
      - intent (6):     factual / explanatory / empathetic / exploratory / clarifying / safety
      - truth (3):      true / false / unknown
      - deductive (3):  entails / contradicts / insufficient
                        (úzce formální: sylogismy, modus ponens/tollens)
      - abductive (4):  correct / plausible / implausible / unrelated
                        (best-explanation ranking: detektivní a archeologický styl)
      - inductive (3):  generalizes / overgeneralizes / undergeneralizes

    Regresní úlohy:
      - emotion (2):    valence, arousal
      - confidence (1): meta-jistota z průměrné entropie ostatních hlav + malá korekce
    """

    def __init__(
        self,
        input_dim: int = 384,
        hidden_dim: int = 256,
        adapter_dim: int = 64,
    ) -> None:
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.10),
        )
        self.adapter = nn.Sequential(
            nn.Linear(hidden_dim, adapter_dim),
            nn.Tanh(),
        )

        self.intent_head = nn.Linear(adapter_dim, 6)
        self.truth_head = nn.Linear(adapter_dim, 3)
        self.deductive_head = nn.Linear(adapter_dim, 3)
        self.abductive_head = nn.Linear(adapter_dim, 4)
        self.inductive_head = nn.Linear(adapter_dim, 3)
        self.emotion_head = nn.Linear(adapter_dim, 2)

        # Confidence = meta-head over entropy of other classification heads
        # + small trainable correction from adapter.
        # Avoids the failure mode where confidence is a memorized phrase->value lookup.
        self.confidence_correction = nn.Linear(adapter_dim, 1)

    def _entropy(self, logits: torch.Tensor) -> torch.Tensor:
        p = torch.softmax(logits, dim=-1)
        eps = 1e-8
        return -(p * torch.log(p + eps)).sum(dim=-1, keepdim=True)

    def forward(self, features: torch.Tensor) -> Dict[str, torch.Tensor]:
        shared = self.shared(features)
        z = self.adapter(shared)

        intent_logits = self.intent_head(z)
        truth_logits = self.truth_head(z)
        deductive_logits = self.deductive_head(z)
        abductive_logits = self.abductive_head(z)
        inductive_logits = self.inductive_head(z)
        emotion = self.emotion_head(z)

        # Normalize entropy per head by its max, then average.
        log6 = torch.log(torch.tensor(6.0, device=features.device))
        log4 = torch.log(torch.tensor(4.0, device=features.device))
        log3 = torch.log(torch.tensor(3.0, device=features.device))

        e_intent = self._entropy(intent_logits) / log6
        e_truth = self._entropy(truth_logits) / log3
        e_deduct = self._entropy(deductive_logits) / log3
        e_abduct = self._entropy(abductive_logits) / log4
        e_induct = self._entropy(inductive_logits) / log3

        mean_entropy = (e_intent + e_truth + e_deduct + e_abduct + e_induct) / 5.0
        base_confidence = 1.0 - mean_entropy
        correction = self.confidence_correction(z)
        confidence_raw = base_confidence + 0.25 * torch.tanh(correction)

        return {
            "adapter": z,
            "intent": intent_logits,
            "truth": truth_logits,
            "deductive": deductive_logits,
            "abductive": abductive_logits,
            "inductive": inductive_logits,
            "emotion": emotion,
            "confidence": confidence_raw,
        }


FCCSV2Model = FCCSV21Model  # backward alias
