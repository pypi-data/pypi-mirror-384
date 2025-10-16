from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.binding_type import BindingType
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class PageCountMetadata(BaseModel):

    binding_type: Annotated[BindingType, enum_by_name_or_value(BindingType), enum_dump_name] = Field(
        alias="bindingType",
    )

    binding_type_id: int = Field(
        alias="bindingTypeId",
    )

    min: int = Field(
        alias="min",
    )

    increment: int = Field(
        alias="increment",
    )

    max: int = Field(
        alias="max",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["PageCountMetadata"]
