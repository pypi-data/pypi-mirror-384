from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class PublicationMetadata(BaseModel):

    supports_self_publishing: bool = Field(
        default=False,
        alias="supportsSelfPublishing",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
    )


__all__ = ["PublicationMetadata"]
