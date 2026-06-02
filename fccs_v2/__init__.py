"""FCCS v2: multi-head cognitive architecture with bio-core bridge.

This vendored copy provides the *inference* surface used by the
MnemoLattice PhantomBridge: config, model, encoders and the predict path.
The full training corpus generator (`data.py`) is not required here — the
cognitive label vocabularies live in the lean `labels.py` module.
"""

from .config import FCCSV2Config
from .model import FCCSV2Model
from .infer import load_bundle, predict_text

__all__ = ["FCCSV2Config", "FCCSV2Model", "load_bundle", "predict_text"]
