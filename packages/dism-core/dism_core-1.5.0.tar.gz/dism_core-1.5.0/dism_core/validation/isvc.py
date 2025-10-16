from pathlib import Path
from typing import TypedDict, Union

from ..properties.isvc.mlserver import (
    LightGBMProperties,
    MLServerProperties,
    SKLearnProperties,
    XGBoostProperties,
)
from ..properties.isvc.tritonserver import (
    ONNXProperties,
    PythonProperties,
    TensorflowSavedModelProperties,
    TorchscriptProperties,
)
from ..resources.isvc.types import ModelType, ServingFrameworkType
from ..resources.types import ResourceType
from ..template import Template
from .utils import has_handler_class


class InferenceServiceValidator:
    def __init__(self, template: Template) -> None:
        self.template = template

    @staticmethod
    def validate_saved_model(props: TensorflowSavedModelProperties) -> None:
        class RequiredFile(TypedDict):
            name: str
            is_file: bool

        required_files: list[RequiredFile] = [
            {"name": "saved_model.pb", "is_file": True},
            {"name": "variables", "is_file": False},
            {"name": "fingerprint.pb", "is_file": True},
        ]
        for req in required_files:
            path_res: Path = props.SavedModelUri / req["name"]
            if req["is_file"]:
                if path_res.is_file() is False:
                    raise ValueError(f'File "{path_res}" not found or is not a file.')
            else:
                if path_res.is_dir() is False:
                    raise ValueError(f'Directory "{path_res}" not found or is not a directory.')

    @staticmethod
    def validate_model_uri(
        props: Union[
            TorchscriptProperties,
            ONNXProperties,
            PythonProperties,
            XGBoostProperties,
            LightGBMProperties,
            SKLearnProperties,
        ],
    ) -> None:
        if props.ModelUri.is_file() is False:
            raise ValueError(f"File {props.ModelUri} not found or is not a file.")

    @staticmethod
    def validate_mlserver_handler(props: MLServerProperties) -> None:
        # Check the handler script exists
        handler_script = "/".join(props.Handler.split(".")[:-1]) + ".py"
        script_path = props.CodeUri / handler_script
        if script_path.is_file() is False:
            raise ValueError(f"File {script_path} not found or is not a file.")

        # Check the handler entrypoint exists in the handler script
        cls_name = props.Handler.split(".")[-1]
        if has_handler_class(script_path, cls_name) is False:
            raise ValueError(f'Handler "{cls_name}" not found in {script_path}')

    @staticmethod
    def validate_triton_python_handler(props: PythonProperties) -> None:
        # Check the handler script exists
        handler_script = "model.py"  # required by triton
        script_path = props.CodeUri / handler_script
        if script_path.is_file() is False:
            raise ValueError(f"File {script_path} not found or is not a file.")

        # Check the handler entrypoint exists in the handler script
        cls_name = "TritonPythonModel"  # required by triton
        if has_handler_class(script_path, cls_name) is False:
            raise ValueError(f'Handler "{cls_name}" not found in {script_path}')

    def __call__(self):
        for _, resource in self.template.Resources.items():
            if resource.SuperType != ResourceType.INFERENCE_SERVICE:
                raise NotImplementedError(f"Resource {resource.Type.value} is not supported")

            if resource.ServingFrameworkType == ServingFrameworkType.TRITONSERVER and resource.ModelType in (
                ModelType.TORCHSCRIPT,
                ModelType.ONNX,
            ):
                self.validate_model_uri(resource.Properties)
            elif resource.ServingFrameworkType == ServingFrameworkType.TRITONSERVER and resource.ModelType in (
                ModelType.PYTHON,
            ):
                self.validate_model_uri(resource.Properties)
                self.validate_triton_python_handler(resource.Properties)
            elif (
                resource.ServingFrameworkType == ServingFrameworkType.TRITONSERVER
                and resource.ModelType == ModelType.TENSORFLOW_SAVEDMODEL
            ):
                self.validate_saved_model(resource.Properties)
            elif resource.ServingFrameworkType == ServingFrameworkType.ML_SERVER and resource.ModelType in (
                ModelType.XGBOOST,
                ModelType.LIGHTGBM,
                ModelType.SKLEARN,
            ):
                self.validate_model_uri(resource.Properties)
                self.validate_mlserver_handler(resource.Properties)
            else:
                raise NotImplementedError(f"Resource {resource.Type.value} is not supported")
