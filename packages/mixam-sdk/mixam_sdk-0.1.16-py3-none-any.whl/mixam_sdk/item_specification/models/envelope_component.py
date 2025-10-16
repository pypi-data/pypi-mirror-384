from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.models.laminated_foiled_component_support import (
    LaminatedFoiledComponentSupport,
)


class EnvelopeComponent(LaminatedFoiledComponentSupport):

    component_type: Literal[ComponentType.ENVELOPE] = Field(
        default=ComponentType.ENVELOPE,
        alias="componentType",
        validation_alias="componentType",
        frozen=True
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )

