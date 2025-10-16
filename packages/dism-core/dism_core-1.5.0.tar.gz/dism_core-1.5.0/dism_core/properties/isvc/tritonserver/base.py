from pathlib import Path
from typing import Optional

from ..base import InferenceServiceProperties
from .types import BackendType, PlatformType


class TritonserverProperties(InferenceServiceProperties):
    MaxBatchSize: int
    ModelRepositoryUri: Optional[Path] = None
    Backend: BackendType
    Platform: Optional[PlatformType] = None

    def __setattr__(self, name, value):
        if name == "Platform":
            raise AttributeError("Platform is a constant and cannot be changed.")
        elif name == "Backend":
            raise AttributeError("Backend is a constant and cannot be changed.")
        super().__setattr__(name, value)
