from pathlib import Path

from .base import TritonserverProperties
from .types import BackendType, PlatformType


class TensorflowSavedModelProperties(TritonserverProperties):
    SavedModelUri: Path
    Backend: BackendType = BackendType.TENSORFLOW
    Platform: PlatformType = PlatformType.TENSORFLOW_SAVEDMODEL
