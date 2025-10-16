from __future__ import annotations

from typing import ClassVar, Dict, Literal, Annotated

from pydantic import Field, ConfigDict

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.enums.simple_fold import SimpleFold
from mixam_sdk.item_specification.interfaces.component_protocol import member_meta
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name
from mixam_sdk.item_specification.models.two_sided_component_support import (
    TwoSidedComponentSupport,
)


class FoldedComponent(TwoSidedComponentSupport):

    FIELDS: ClassVar[Dict[str, str]] = {
        "simple_fold": "d",
        "sides": "s",
        "flat_on_delivery": "t",
    }

    component_type: Literal[ComponentType.FOLDED] = Field(
        default=ComponentType.FOLDED,
        alias="componentType",
        validation_alias="componentType",
        frozen=True
    )

    simple_fold: Annotated[SimpleFold, enum_by_name_or_value(SimpleFold), enum_dump_name] = Field(
        default=SimpleFold.NONE,
        alias="simpleFold",
        description="Type of simple fold for the component.",
        json_schema_extra=member_meta(FIELDS["simple_fold"]),
    )

    sides: int = Field(
        default=0,
        description="Number of sides/panels for the folded item.",
        json_schema_extra=member_meta(FIELDS["sides"]),
    )

    flat_on_delivery: bool = Field(
        default=False,
        alias="flatOnDelivery",
        description="Indicates if the item should be delivered flat instead of folded.",
        json_schema_extra=member_meta(FIELDS["flat_on_delivery"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )

    def is_folded(self) -> bool:
        return SimpleFold(self.simple_fold) != SimpleFold.NONE
