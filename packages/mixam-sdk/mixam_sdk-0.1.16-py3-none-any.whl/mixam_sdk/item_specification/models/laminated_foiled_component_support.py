from __future__ import annotations

from typing import ClassVar, Dict

from pydantic import Field, ConfigDict

from mixam_sdk.item_specification.interfaces.component_protocol import container_meta
from mixam_sdk.item_specification.models.foiling import Foiling
from mixam_sdk.item_specification.models.laminated_component_support import (
    LaminatedComponentSupport,
)


class LaminatedFoiledComponentSupport(LaminatedComponentSupport):

    FIELDS: ClassVar[Dict[str, str]] = {
        "foiling": "f",
    }

    foiling: Foiling = Field(
        default_factory=Foiling,
        description="Foiling details of the component.",
        json_schema_extra=container_meta(FIELDS["foiling"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )

