from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.metadata.product.models.shrink_wrap_option import ShrinkWrapOption


class ShrinkWrapMetadata(BaseModel):

    options: list[ShrinkWrapOption] = Field(
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["ShrinkWrapMetadata"]
