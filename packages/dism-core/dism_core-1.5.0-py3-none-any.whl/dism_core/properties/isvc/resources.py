from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ResourceSpec(BaseModel):
    cpu: Optional[str] = None
    memory: Optional[str] = None
    gpu: Optional[str] = Field(default=None, alias="nvidia.com/gpu")

    model_config = ConfigDict(populate_by_name=True)


class Resources(BaseModel):
    Requests: Optional[ResourceSpec] = None
    Limits: Optional[ResourceSpec] = None
