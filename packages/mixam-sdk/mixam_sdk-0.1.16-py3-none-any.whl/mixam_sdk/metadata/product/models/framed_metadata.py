from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.metadata.product.models.frame_depth_option import FrameDepthOption


class FramedMetadata(BaseModel):

    frame_depth_options: list[FrameDepthOption] = Field(
        alias="frameDepthOptions",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["FramedMetadata"]
