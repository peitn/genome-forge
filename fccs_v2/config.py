from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict


@dataclass
class EncoderConfig:
    mode: str = "auto"  # auto | hash | sentence-transformer
    embedding_dim: int = 384
    hash_buckets: int = 4096
    seed: int = 13
    sentence_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@dataclass
class TrainConfig:
    epochs: int = 6
    batch_size: int = 32
    lr: float = 1e-3
    weight_decay: float = 1e-4
    hidden_dim: int = 256
    adapter_dim: int = 64
    seed: int = 13
    train_fraction: float = 0.8
    intent_weight: float = 1.0
    truth_weight: float = 1.0
    deductive_weight: float = 1.0
    abductive_weight: float = 1.0
    inductive_weight: float = 1.0
    emotion_weight: float = 0.75
    confidence_weight: float = 0.5


@dataclass
class FCCSV2Config:
    encoder: EncoderConfig = field(default_factory=EncoderConfig)
    train: TrainConfig = field(default_factory=TrainConfig)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)

    def save_json(self, output_dir: str | Path) -> Path:
        import json

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "config.json"
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path

    @classmethod
    def from_json(cls, path: str | Path) -> "FCCSV2Config":
        import json

        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            encoder=EncoderConfig(**raw["encoder"]),
            train=TrainConfig(**raw["train"]),
        )
