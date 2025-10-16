from enum import Enum

from pydantic import BaseModel


class DataTypeEnum(str, Enum):
    BOOL = "BOOL"
    UINT8 = "UINT8"
    UINT16 = "UINT16"
    UINT32 = "UINT32"
    UINT64 = "UINT64"
    INT8 = "INT8"
    INT16 = "INT16"
    INT32 = "INT32"
    INT64 = "INT64"
    FP16 = "FP16"
    FP32 = "FP32"
    FP64 = "FP64"
    BYTES = "BYTES"

    @classmethod
    def _missing_(cls, value):
        """
        Accept old names like "TYPE_UINT8" by stripping the TYPE_ prefix.
        """
        if isinstance(value, str) and value.startswith("TYPE_"):
            stripped = value[5:]  # remove 'TYPE_'
            for member in cls:
                if member.value == stripped:
                    return member
        return None


class BaseSignature(BaseModel):
    DataType: DataTypeEnum
    Dims: list[int]
    Name: str


class InputSignature(BaseSignature):
    MonitoringElement: str


class OutputSignature(BaseSignature):
    pass
