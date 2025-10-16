import re
from re import Pattern
from typing import Optional

from pydantic import BaseModel, model_validator


class InferenceOnConditions(BaseModel):
    MinRunNumber: Optional[int] = None
    MaxRunNumber: Optional[int] = None
    StableBeams: Optional[bool] = None
    FillType: Optional[str] = None
    MinNumberOfLumisection: Optional[int] = None
    MinDeliveredLuminosity: Optional[float] = None
    MinRecordedLuminosity: Optional[float] = None
    MinBField: Optional[float] = None
    MinEnergy: Optional[float] = None
    Clock: Optional[str] = None
    Sequence: Optional[str] = None
    L1KeyMatch: Optional[Pattern] = None
    L1MenuMatch: Optional[Pattern] = None
    HLTConfigMatch: Optional[Pattern] = None
    NoComponentOut: Optional[bool] = None
    AllowedComponentsOut: Optional[list[str]] = None
    AllowedPrimaryDatasets: Optional[list[str]] = None

    @model_validator(mode="after")
    def check_components_props(self) -> "InferenceOnConditions":
        if self.NoComponentOut is not None and self.AllowedComponentsOut is not None:
            raise ValueError("The `NoComponentOut` field cannot be declared if `AllowedComponentsOut` is provided.")
        return self

    @model_validator(mode="before")
    @classmethod
    def compile_regex(cls, values):
        regex_fields = ["L1KeyMatch", "L1MenuMatch", "HLTConfigMatch"]
        for field in regex_fields:
            if isinstance(values.get(field), str):
                values[field] = re.compile(values[field])
        return values
