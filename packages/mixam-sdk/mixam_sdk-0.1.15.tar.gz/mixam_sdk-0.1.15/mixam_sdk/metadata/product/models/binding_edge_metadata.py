from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.binding_edge import BindingEdge
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class BindingEdgeMetadata(BaseModel):

    binding_edge: Annotated[BindingEdge, enum_by_name_or_value(BindingEdge), enum_dump_name] = Field(
        alias="bindingEdge",
    )

    label: str = Field()

    santa_default: bool = Field(
        default=False,
        alias="santaDefault",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["BindingEdgeMetadata"]
