from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict, computed_field

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class ComponentRequirement(BaseModel):

    component_type: Annotated[ComponentType, enum_by_name_or_value(ComponentType), enum_dump_name] = Field(
        alias="componentType",
    )

    minimum_instances: int = Field(
        default=0,
        alias="minimumInstances",
    )

    maximum_instances: int = Field(
        default=1,
        alias="maximumInstances",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )

    @computed_field
    @property
    def isRequired(self) -> bool:
        return self.minimum_instances > 0


__all__ = ["ComponentRequirement"]
