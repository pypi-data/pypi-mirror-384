from typing import Union

from pydantic import BaseModel, Field, model_validator

from ...properties.isvc.mlserver import (
    LightGBMProperties,
    SKLearnProperties,
    XGBoostProperties,
)
from ...properties.isvc.tritonserver import (
    ONNXProperties,
    PythonProperties,
    TensorflowSavedModelProperties,
    TorchscriptProperties,
)
from ..types import ResourceType
from .types import ModelType, ServingFrameworkType


class InferenceServiceResource(BaseModel):
    SuperType: ResourceType
    ServingFrameworkType: ServingFrameworkType
    ModelType: ModelType
    Type: str
    Workspace: str
    Properties: Union[
        TorchscriptProperties,
        TensorflowSavedModelProperties,
        ONNXProperties,
        PythonProperties,
        XGBoostProperties,
        LightGBMProperties,
        SKLearnProperties,
    ] = Field(...)

    @model_validator(mode="before")
    @classmethod
    def validate_and_map_props(cls, resource):
        try:
            super_type, framework, model = resource["Type"].split("::")
        except ValueError as err:
            raise ValueError(
                f"Invalid Type format: {resource['Type']}. Expected format: 'SuperType::Framework::Model'."
            ) from err

        # Validate the components
        if super_type != ResourceType.INFERENCE_SERVICE:
            raise NotImplementedError(f"Unsupported SuperType: {super_type}")
        if framework not in ServingFrameworkType.__members__.values():
            raise NotImplementedError(f"Unsupported ServingFramework: {framework}")
        if model not in ModelType.__members__.values():
            raise NotImplementedError(f"Unsupported ModelType: {model}")

        # Map the resource to the appropriate properties
        if (framework, model) == (ServingFrameworkType.TRITONSERVER, ModelType.TORCHSCRIPT):
            props = TorchscriptProperties(**resource["Properties"])
        elif (framework, model) == (ServingFrameworkType.TRITONSERVER, ModelType.TENSORFLOW_SAVEDMODEL):
            props = TensorflowSavedModelProperties(**resource["Properties"])
        elif (framework, model) == (ServingFrameworkType.TRITONSERVER, ModelType.ONNX):
            props = ONNXProperties(**resource["Properties"])
        elif (framework, model) == (ServingFrameworkType.TRITONSERVER, ModelType.PYTHON):
            props = PythonProperties(**resource["Properties"])
        elif (framework, model) == (ServingFrameworkType.ML_SERVER, ModelType.XGBOOST):
            props = XGBoostProperties(**resource["Properties"])
        elif (framework, model) == (ServingFrameworkType.ML_SERVER, ModelType.LIGHTGBM):
            props = LightGBMProperties(**resource["Properties"])
        elif (framework, model) == (ServingFrameworkType.ML_SERVER, ModelType.SKLEARN):
            props = SKLearnProperties(**resource["Properties"])
        else:
            raise NotImplementedError(f"Resource of type {resource['Type']} is not supported.")

        # Update the resource with the mapped properties
        resource["SuperType"] = ResourceType(super_type)
        resource["ServingFrameworkType"] = ServingFrameworkType(framework)
        resource["ModelType"] = ModelType(model)
        resource["Properties"] = props
        return resource

    @model_validator(mode="after")
    def check_output_signature(self) -> "InferenceServiceResource":
        flagging_key = self.Properties.FlaggingKey
        metric_key = self.Properties.MetricKey
        output_names = [sig.Name for sig in self.Properties.OutputSignature]
        if flagging_key and flagging_key not in output_names:
            raise ValueError(f'FlaggingKey "{flagging_key}" not found in OutputSignature')
        if metric_key and metric_key not in output_names:
            raise ValueError(f'MetricKey "{metric_key}" not found in OutputSignature')
        return self
