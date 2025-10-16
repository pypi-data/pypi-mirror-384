from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field, ConfigDict

from .binding_edge_metadata import BindingEdgeMetadata
from .binding_type_option import BindingTypeOption
from .end_paper_metadata import EndPaperMetadata
from .head_and_tail_band_metadata import HeadAndTailBandMetadata
from .ribbon_metadata import RibbonMetadata


class BoundMetadata(BaseModel):

    DEFAULT_GLOBAL_MAX_PAGES: ClassVar[int] = 2000

    pages_increment: int = Field(
        alias="pagesIncrement",
    )

    default_pages: int = Field(
        alias="defaultPages",
    )

    pages_per_leaf: int = Field(
        alias="pagesPerLeaf",
    )

    ribbon_metadata: list[RibbonMetadata] = Field(
        alias="ribbonMetadata",
    )

    head_and_tail_band_metadata: list[HeadAndTailBandMetadata] = Field(
        alias="headAndTailBandMetadata",
    )

    end_paper_metadata: list[EndPaperMetadata] = Field(
        alias="endPaperMetadata",
    )

    binding_type_options: list[BindingTypeOption] = Field(
        alias="bindingTypeOptions",
    )

    binding_edge_options: list[BindingEdgeMetadata] = Field(
        alias="bindingEdgeOptions",
    )

    global_min_pages: int | None = Field(
        default=None,
        alias="globalMinPages",
    )

    global_max_pages: int | None = Field(
        default=None,
        alias="globalMaxPages",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["BoundMetadata"]
