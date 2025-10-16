from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.simple_fold import SimpleFold
from mixam_sdk.metadata.product.enums.trilean import Trilean
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class SimpleFoldOption(BaseModel):

    simple_fold: Annotated[SimpleFold, enum_by_name_or_value(SimpleFold), enum_dump_name] = Field(
        alias="simpleFold",
    )

    label: str = Field()

    value: int = Field()

    available_sides: list[int] = Field(
        default_factory=list,
        alias="availableSides",
    )

    delivered_flat: Annotated[Trilean, enum_by_name_or_value(Trilean), enum_dump_name] = Field(
        alias="deliveredFlat",
    )

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


__all__ = ["SimpleFoldOption"]
