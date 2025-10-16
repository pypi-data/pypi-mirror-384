from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.metadata.product.models.foiling_option import FoilingOption


class FoilingMetadata(BaseModel):

    cover_foiling: list[FoilingOption] = Field(
        alias="coverFoiling",
    )

    dust_jacket_foiling: list[FoilingOption] = Field(
        alias="dustJacketFoiling",
    )

    front_foiling: list[FoilingOption] = Field(
        alias="frontFoiling",
    )

    back_foiling: list[FoilingOption] = Field(
        alias="backFoiling",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["FoilingMetadata"]
