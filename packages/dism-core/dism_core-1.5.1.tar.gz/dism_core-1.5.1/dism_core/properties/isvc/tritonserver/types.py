from enum import Enum


class PlatformType(str, Enum):
    TORCHSCRIPT = "pytorch_libtorch"
    TENSORFLOW_SAVEDMODEL = "tensorflow_savedmodel"
    ONNX = "onnxruntime_onnx"


class BackendType(str, Enum):
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    ONNX = "onnxruntime"
    PYTHON = "python"
