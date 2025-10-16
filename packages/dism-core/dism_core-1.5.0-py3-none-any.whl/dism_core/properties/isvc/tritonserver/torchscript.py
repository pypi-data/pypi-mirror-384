from pathlib import Path

from .base import TritonserverProperties
from .types import BackendType, PlatformType


class TorchscriptProperties(TritonserverProperties):
    ModelUri: Path
    Backend: BackendType = BackendType.PYTORCH
    Platform: PlatformType = PlatformType.TORCHSCRIPT
