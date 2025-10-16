from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.metadata.product.models.flap_width_option import FlapWidthOption


class FlapMetadata(BaseModel):

    flap_width_options: list[FlapWidthOption] = Field(
        alias="flapWidthOptions",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["FlapMetadata"]
