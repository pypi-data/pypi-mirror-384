from pathlib import Path

from .base import TritonserverProperties
from .types import BackendType, PlatformType


class ONNXProperties(TritonserverProperties):
    ModelUri: Path
    Backend: BackendType = BackendType.ONNX
    Platform: PlatformType = PlatformType.ONNX
