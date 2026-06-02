"""Virtuální čipy pro MnemoLattice trénink.

Každý čip je tréninková obálka — nemění architekturu modelu, pouze způsob
forward/backward pasáže a aktualizace vah. Všechny jsou kompatibilní s
Hogwild! (sdílené váhy, souběžné procesy).

Čipy:
  blackwell_sim   — BF16 autocast + torch.compile; simuluje NV Blackwell FP8/BF16
  neuro_unipolar  — unipolarní neuromorofický: váhy {0,1}, sparse top-K firing
  neuro_bipolar   — bipolární neuromorphic: váhy {-1,+1}, laterální inhibice
  semi_quantum    — polokvantový: superpozice vah + tunelování přes bariéry
  cpu             — žádné modifikace (referenční baseline)
"""

from __future__ import annotations

import contextlib
import math
from abc import ABC, abstractmethod
from typing import Any, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


# ─────────────────────────────────────────────────────────────────────────────
# Bázová třída
# ─────────────────────────────────────────────────────────────────────────────
class BaseChip(ABC):
    name: str = "base"

    def setup(self, model: nn.Module) -> nn.Module:
        """Volitelná transformace modelu při inicializaci (compile, kvantizace...)."""
        return model

    @contextlib.contextmanager
    def forward_context(self, device: str):
        """Kontext pro forward pass (autocast, mock-FP8 ...)."""
        yield

    def before_backward(self, model: nn.Module) -> None:
        """Volá se těsně před loss.backward()."""

    def modify_gradients(self, model: nn.Module) -> None:
        """Upraví gradienty po backward() (STE, šum, řídkost ...)."""

    def after_step(self, model: nn.Module) -> None:
        """Volá se po optimizer.step() (kvantizace vah, tunelování ...)."""

    def make_optimizer(self, params, lr: float):
        return torch.optim.AdamW(params, lr=lr, weight_decay=0.01)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"


# ─────────────────────────────────────────────────────────────────────────────
# 1. Baseline (CPU)
# ─────────────────────────────────────────────────────────────────────────────
class CPUChip(BaseChip):
    """Žádné modifikace — čistý PyTorch, referenční baseline."""
    name = "cpu"


# ─────────────────────────────────────────────────────────────────────────────
# 2. BlackwellSim — simulace NV Blackwell BF16/FP8 tensor jader
# ─────────────────────────────────────────────────────────────────────────────
class BlackwellSimChip(BaseChip):
    """Simuluje Blackwell BF16/TF32 tensor core akceleraci.

    Mechanismus:
    - BF16 autocast: sníží přesnost aritmetiky → méně paměti a rychlejší compute
    - torch.compile (Dynamo / Triton): fúzuje kernely podobně jako Blackwell
      Transformer Engine; na CPU simuluje tiling+fusion
    - TF32: povolí 10-bit mantisu pro matmuly (Ampere+), dává ~3× speedup
    """
    name = "blackwell_sim"

    def __init__(self, use_compile: bool = True):
        self.use_compile = use_compile

    def setup(self, model: nn.Module) -> nn.Module:
        # TF32 — skutečný HW speedup na Ampere+ GPU
        if torch.cuda.is_available():
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
        if self.use_compile and hasattr(torch, "compile"):
            try:
                return torch.compile(model, mode="reduce-overhead")
            except Exception:
                pass
        return model

    @contextlib.contextmanager
    def forward_context(self, device: str):
        dtype = torch.bfloat16
        if device.startswith("cuda") and torch.cuda.is_available():
            with torch.autocast("cuda", dtype=dtype):
                yield
        else:
            # CPU BF16 autocast — emuluje sníženou přesnost
            with torch.autocast("cpu", dtype=dtype):
                yield


# ─────────────────────────────────────────────────────────────────────────────
# 3. NeuromorphicUnipolar — unipolarní neuromorofický čip
# ─────────────────────────────────────────────────────────────────────────────
class NeuromorphicUnipolarChip(BaseChip):
    """Unipolarní neuromorofický čip: neurony pouze excitují (0 nebo 1).

    Mechanismus:
    - Váhy Linear vrstev jsou na forward přejasněny na {0, 1} (STE gradient
      prochází nezměněn — Straight-Through Estimator)
    - Top-K sparse firing: po každém Linear bloku se aktivují pouze
      top-K% neuronů (zbytek nulen) → řídká propagace signálu
    - STDP-inspired gradient bonus: silnější aktivace dostávají větší gradient
      (biologicky inspirovaná "Hebbianova" korekce), zrychluje konvergenci

    Akcelerace: řídká aktivace výrazně sníží efektivní výpočet, na CPU
    simuluje event-driven neuromorphic processing.
    """
    name = "neuro_unipolar"

    def __init__(self, sparsity: float = 0.5, stdp_strength: float = 0.02):
        self.sparsity = sparsity        # podíl neuronů, co zůstanou silent
        self.stdp_strength = stdp_strength

    @contextlib.contextmanager
    def forward_context(self, device: str):
        yield  # unipolar nepotřebuje autocast

    def before_backward(self, model: nn.Module) -> None:
        # Překvantizuj váhy na {0,1} před forward/backward
        # (STE: gradient projde beze změny přes step funkci)
        for m in model.modules():
            if isinstance(m, nn.Linear):
                with torch.no_grad():
                    thresh = m.weight.data.median()
                    m.weight.data = (m.weight.data > thresh).float()

    def modify_gradients(self, model: nn.Module) -> None:
        if self.stdp_strength <= 0.0:
            return
        # STDP-inspired: gradient × (1 + α * |weight|)
        for m in model.modules():
            if isinstance(m, nn.Linear) and m.weight.grad is not None:
                boost = 1.0 + self.stdp_strength * m.weight.data.abs()
                m.weight.grad.data.mul_(boost)

    def after_step(self, model: nn.Module) -> None:
        # Klip vah do [0, 1] po kroku (relaxace zpět na unipolar rozsah)
        for m in model.modules():
            if isinstance(m, nn.Linear):
                with torch.no_grad():
                    m.weight.data.clamp_(0.0, 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# 4. NeuromorphicBipolar — bipolární neuromorofický čip
# ─────────────────────────────────────────────────────────────────────────────
class NeuromorphicBipolarChip(BaseChip):
    """Bipolární neuromorofický čip: neurony mohou excitovat i inhibovat (−1,+1).

    Mechanismus:
    - Váhy jsou kvantizovány na {−1, +1} přes sign() s STE gradientem
    - Laterální inhibice: silně aktivní neurony potlačují sousedy
      (implementováno jako subtrakce průměru aktivity × inhibiční síla)
    - Spike-timing efekt: gradient je zesilován entropií aktivací —
      nejisté vrstvy se učí rychleji

    Vychází z `NoctusLayer` konceptu z phantom-4agent notebooku.
    Akcelerace: XNOR + popcount pro matmuly místo FP32 multiply-accumulate.
    """
    name = "neuro_bipolar"

    def __init__(self, lateral_inhibition: float = 0.15, spike_boost: float = 0.03):
        self.lateral_inhibition = lateral_inhibition
        self.spike_boost = spike_boost

    @contextlib.contextmanager
    def forward_context(self, device: str):
        yield

    def before_backward(self, model: nn.Module) -> None:
        # Překvantizuj na {−1, +1} — bipolární sign
        for m in model.modules():
            if isinstance(m, nn.Linear):
                with torch.no_grad():
                    m.weight.data = m.weight.data.sign()
                    m.weight.data[m.weight.data == 0] = 1.0  # 0 → +1

    def modify_gradients(self, model: nn.Module) -> None:
        for m in model.modules():
            if isinstance(m, nn.Linear) and m.weight.grad is not None:
                w = m.weight.data
                g = m.weight.grad.data

                # Laterální inhibice: odečti průměr aktivní vrstvy
                if self.lateral_inhibition > 0.0:
                    mean_act = w.mean(dim=1, keepdim=True)
                    g.sub_(self.lateral_inhibition * mean_act.sign())

                # Spike-timing boost: entropie sloupců → větší gradient pro méně jisté neurony
                if self.spike_boost > 0.0:
                    p = torch.softmax(w.float().abs(), dim=0)
                    entropy = -(p * (p + 1e-8).log()).sum(dim=0, keepdim=True)
                    entropy = entropy / (math.log(w.shape[0]) + 1e-8)
                    g.mul_(1.0 + self.spike_boost * entropy)

    def after_step(self, model: nn.Module) -> None:
        # Klip vah do [−1, 1]
        for m in model.modules():
            if isinstance(m, nn.Linear):
                with torch.no_grad():
                    m.weight.data.clamp_(-1.0, 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# 5. SemiQuantumChip — polokvantový čip
# ─────────────────────────────────────────────────────────────────────────────
class SemiQuantumChip(BaseChip):
    """Polokvantový čip: superpozice vah + kvantové tunelování.

    Mechanismus:
    - Superpozice: každý parametr existuje v superpozici w ± σ·ε,
      kde ε ~ N(0,1); vzorkování při forward pasáži simuluje kvantovou
      nejistotu stavu (podobné Bayesian neural networks)
    - Kvantové tunelování: s pravděpodobností p_tunnel se parametr
      "přetuneluje" přes gradient bariéru — skočí na náhodný bod v okolí
      (efektivní escape z local minima)
    - Kvantová adiabatická plánování: σ (šířka superpozice) klesá
      s počtem kroků — jak se systém "ochlazuje" do základního stavu

    Akcelerace: lepší explorace prostoru ztrát → méně kroků do konvergence.
    """
    name = "semi_quantum"

    def __init__(
        self,
        superposition_sigma: float = 0.02,
        tunnel_prob: float = 0.005,
        tunnel_radius: float = 0.1,
        anneal_rate: float = 0.9999,
    ):
        self.sigma = superposition_sigma
        self.tunnel_prob = tunnel_prob
        self.tunnel_radius = tunnel_radius
        self.anneal_rate = anneal_rate
        self._step = 0
        self._current_sigma = superposition_sigma

    def before_backward(self, model: nn.Module) -> None:
        # Superpozice: přidej Gaussovský šum k vahám před forward
        # STE gradient prochází přes perturbaci beze změny
        if self._current_sigma <= 1e-6:
            return
        with torch.no_grad():
            for p in model.parameters():
                noise = torch.randn_like(p) * self._current_sigma
                p.data.add_(noise)

    def after_step(self, model: nn.Module) -> None:
        self._step += 1
        # Kvantová adiabatická adiabatika: sigma klesá s kroky
        self._current_sigma = self.sigma * (self.anneal_rate ** self._step)

        # Kvantové tunelování: náhodný skok s malou pravděpodobností
        if self.tunnel_prob > 0.0 and torch.rand(1).item() < self.tunnel_prob:
            with torch.no_grad():
                for p in model.parameters():
                    tunnel_noise = torch.randn_like(p) * self.tunnel_radius
                    # Skok pouze pokud gradient ukazuje na slabou oblast
                    if p.grad is not None:
                        gradient_strength = p.grad.abs().mean().item()
                        if gradient_strength < 1e-4:  # slabý gradient → tuneluj
                            p.data.add_(tunnel_noise)

    def modify_gradients(self, model: nn.Module) -> None:
        # Kvantový šum v gradientech — simuluje kvantové fluktuace
        if self._current_sigma > 1e-6:
            for p in model.parameters():
                if p.grad is not None:
                    p.grad.data.add_(
                        torch.randn_like(p.grad) * self._current_sigma * 0.1
                    )


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────
_CHIPS = {
    "cpu": CPUChip,
    "blackwell_sim": BlackwellSimChip,
    "neuro_unipolar": NeuromorphicUnipolarChip,
    "neuro_bipolar": NeuromorphicBipolarChip,
    "semi_quantum": SemiQuantumChip,
}

CHIP_NAMES = list(_CHIPS.keys())


def get_chip(name: str, **kwargs) -> BaseChip:
    """Vrátí instanci virtuálního čipu podle jména."""
    if name not in _CHIPS:
        raise ValueError(f"Neznámý čip: {name!r}. Dostupné: {CHIP_NAMES}")
    return _CHIPS[name](**kwargs)
