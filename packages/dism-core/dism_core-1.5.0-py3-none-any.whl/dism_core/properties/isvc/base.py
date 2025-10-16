from typing import Optional

from pydantic import model_validator

from ..base import BaseProperties
from .inference_cond import InferenceOnConditions as InferenceOnConditionsModel
from .metadata import InputMetadata as InputMeta
from .resources import Resources as ResourcesModel
from .signature import InputSignature, OutputSignature


class InferenceServiceProperties(BaseProperties):
    AnomalyThreshold: Optional[float] = None
    BuiltinThreshold: bool
    FlaggingKey: Optional[str] = None
    InputSignature: list[InputSignature]
    MetricKey: Optional[str] = None
    OutputSignature: list[OutputSignature]
    Image: Optional[str] = None
    Resources: Optional[ResourcesModel] = None
    InferenceOnConditions: Optional[InferenceOnConditionsModel] = None
    InputMetadata: Optional[list[InputMeta]] = None

    @model_validator(mode="after")
    def validate_threshold_logic(self) -> "InferenceServiceProperties":
        # Option A: AnomalyThreshold + MetricKey + BuiltinThreshold == False
        option_a = self.BuiltinThreshold is False and self.AnomalyThreshold is not None and self.MetricKey is not None
        if option_a and self.FlaggingKey is not None:
            raise ValueError("Invalid configuration.\nFlaggingKey cannot be set if BuiltinThreshold = false")

        # Option B: BuiltinThreshold == True + FlaggingKey + [OPTIONAL] MetricKey
        option_b = self.BuiltinThreshold is True and self.FlaggingKey is not None
        if option_b and self.AnomalyThreshold is not None:
            raise ValueError("Invalid configuration.\nAnomalyThreshold cannot be set if BuiltinThreshold = true")

        if not (option_a or option_b):
            raise ValueError(
                "Invalid configuration. You must specify either:\n"
                "- AnomalyThreshold (not None) and MetricKey (not None) with BuiltinThreshold = False\n"
                "OR\n"
                "- BuiltinThreshold = True and FlaggingKey (not None)."
            )

        return self
