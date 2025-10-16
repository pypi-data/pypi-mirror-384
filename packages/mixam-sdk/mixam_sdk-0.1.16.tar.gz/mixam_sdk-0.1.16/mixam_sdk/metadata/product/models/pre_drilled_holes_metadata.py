from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.metadata.product.models.pre_drilled_hole_option import PreDrilledHoleOption


class PreDrilledHolesMetadata(BaseModel):

    pre_drilled_hole_options: list[PreDrilledHoleOption] = Field(
        alias="preDrilledHoleOptions",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["PreDrilledHolesMetadata"]
