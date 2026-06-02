from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Iterable, List

import numpy as np
import torch

_WORD_RE = re.compile(r"[\w']+", flags=re.UNICODE)


class AudioEncoder:
    def encode(self, _: Iterable[object]) -> torch.Tensor:
        raise NotImplementedError(
            "AudioEncoder is intentionally a stub in v2. Plug in wav2vec, whisper, or mel-CNN later."
        )


class VisionEncoder:
    def encode(self, _: Iterable[object]) -> torch.Tensor:
        raise NotImplementedError(
            "VisionEncoder is intentionally a stub in v2. Plug in CLIP/ViT later."
        )


@dataclass
class EncoderInfo:
    backend: str
    embedding_dim: int


class BaseTextEncoder:
    def __init__(self, embedding_dim: int) -> None:
        self.embedding_dim = embedding_dim

    def encode(self, texts: Iterable[str]) -> torch.Tensor:
        raise NotImplementedError

    @property
    def info(self) -> EncoderInfo:
        raise NotImplementedError


class HashProjectionTextEncoder(BaseTextEncoder):
    def __init__(self, embedding_dim: int = 384, hash_buckets: int = 4096, seed: int = 13) -> None:
        super().__init__(embedding_dim=embedding_dim)
        self.hash_buckets = hash_buckets
        self.seed = seed
        rng = np.random.default_rng(seed)
        self._projection = rng.normal(
            loc=0.0,
            scale=1.0 / math.sqrt(hash_buckets),
            size=(hash_buckets, embedding_dim),
        ).astype(np.float32)

    @staticmethod
    def _stable_hash(text: str) -> int:
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
        return int(digest[:16], 16)

    @staticmethod
    def _char_ngrams(text: str, n_min: int = 3, n_max: int = 5) -> List[str]:
        compact = re.sub(r"\s+", " ", text.lower()).strip()
        padded = f"<{compact}>"
        grams: List[str] = []
        for n in range(n_min, n_max + 1):
            grams.extend(padded[i : i + n] for i in range(max(0, len(padded) - n + 1)))
        return grams

    def _encode_one(self, text: str) -> np.ndarray:
        words = [w.lower() for w in _WORD_RE.findall(text)]
        chars = self._char_ngrams(text)
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        total_weight = 1e-6

        for token in words:
            idx = self._stable_hash(f"w::{token}") % self.hash_buckets
            vec += 1.0 * self._projection[idx]
            total_weight += 1.0
        for gram in chars:
            idx = self._stable_hash(f"c::{gram}") % self.hash_buckets
            vec += 0.35 * self._projection[idx]
            total_weight += 0.35

        vec /= total_weight
        norm = float(np.linalg.norm(vec) + 1e-8)
        vec /= norm
        return vec

    def encode(self, texts: Iterable[str]) -> torch.Tensor:
        arr = np.stack([self._encode_one(text) for text in texts], axis=0)
        return torch.from_numpy(arr)

    @property
    def info(self) -> EncoderInfo:
        return EncoderInfo(backend="hash_projection", embedding_dim=self.embedding_dim)


class SentenceTransformerTextEncoder(BaseTextEncoder):
    def __init__(self, model_name: str, embedding_dim: int) -> None:
        super().__init__(embedding_dim=embedding_dim)
        from sentence_transformers import SentenceTransformer  # type: ignore

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: Iterable[str]) -> torch.Tensor:
        arr = self.model.encode(list(texts), normalize_embeddings=True)
        arr = np.asarray(arr, dtype=np.float32)
        return torch.from_numpy(arr)

    @property
    def info(self) -> EncoderInfo:
        return EncoderInfo(backend=f"sentence_transformer::{self.model_name}", embedding_dim=self.embedding_dim)


class AutoTextEncoder(BaseTextEncoder):
    def __init__(
        self,
        mode: str = "auto",
        embedding_dim: int = 384,
        hash_buckets: int = 4096,
        seed: int = 13,
        sentence_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ) -> None:
        super().__init__(embedding_dim=embedding_dim)
        self.mode = mode
        self.sentence_model_name = sentence_model_name
        self._backend: BaseTextEncoder

        if mode == "sentence-transformer":
            self._backend = SentenceTransformerTextEncoder(sentence_model_name, embedding_dim)
        elif mode == "hash":
            self._backend = HashProjectionTextEncoder(embedding_dim, hash_buckets, seed)
        else:
            try:
                self._backend = SentenceTransformerTextEncoder(sentence_model_name, embedding_dim)
            except Exception:
                self._backend = HashProjectionTextEncoder(embedding_dim, hash_buckets, seed)

    def encode(self, texts: Iterable[str]) -> torch.Tensor:
        return self._backend.encode(texts)

    @property
    def info(self) -> EncoderInfo:
        return self._backend.info
