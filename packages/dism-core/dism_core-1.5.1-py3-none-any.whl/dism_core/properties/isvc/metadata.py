import re
from enum import Enum
from re import Pattern
from typing import Optional, Union

from pydantic import BaseModel, model_validator

from .signature import BaseSignature


class SourceEnum(str, Enum):
    OMS = "OMS"


class EndpointEnum(str, Enum):
    lumisections = "lumisections"
    hltpathrates = "hltpathrates"
    datasetrates = "datasetrates"


class FilterOperationEnum(str, Enum):
    EQ = "EQ"
    LIST_AND_MATCH = "LIST_AND_MATCH"


class EndpointFilter(BaseModel):
    Name: str
    Value: Union[str, Pattern]
    Operation: FilterOperationEnum = FilterOperationEnum.EQ

    @model_validator(mode="before")
    @classmethod
    def compile_regex(cls, values):
        if isinstance(values.get("Value"), str) and values.get("Operation") == FilterOperationEnum.LIST_AND_MATCH:
            values["Value"] = re.compile(values["Value"])
        return values


class InputMetadata(BaseModel):
    Name: str
    Source: SourceEnum
    Endpoint: EndpointEnum
    Attributes: list[BaseSignature]
    Filter: Optional[list[EndpointFilter]] = None

    @model_validator(mode="after")
    def check_list_and_match_only_for_hltpathrates(self) -> "InputMetadata":
        if self.Filter:
            for f in self.Filter:
                if f.Operation == FilterOperationEnum.LIST_AND_MATCH and (
                    self.Endpoint != EndpointEnum.hltpathrates or f.Name != "path_name"
                ):
                    raise ValueError(
                        f"LIST_AND_MATCH operation can only be used with Endpoint '{EndpointEnum.hltpathrates}'. "
                        f"Got '{self.Endpoint}' instead."
                    )
        return self
