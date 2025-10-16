from __future__ import annotations

from typing import Literal, Annotated

from pydantic import ConfigDict, Field

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.models.component_support import ComponentSupport


class EndPapersComponent(ComponentSupport):

    component_type: Literal[ComponentType.END_PAPERS] = Field(
        default=ComponentType.END_PAPERS,
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

