from pathlib import Path

from .base import TritonserverProperties
from .types import BackendType


class PythonProperties(TritonserverProperties):
    CodeUri: Path
    ModelUri: Path
    Backend: BackendType = BackendType.PYTHON
