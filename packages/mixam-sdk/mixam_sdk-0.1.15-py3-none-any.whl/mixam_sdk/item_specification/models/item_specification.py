from __future__ import annotations

from typing import List, Annotated, Union

from pydantic import BaseModel, Field, ConfigDict, model_validator

from mixam_sdk.item_specification.enums.colours import Colours
from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.enums.product import Product
from mixam_sdk.item_specification.enums.standard_size import StandardSize
from mixam_sdk.item_specification.models.bound_component import BoundComponent
from mixam_sdk.item_specification.models.component_support import ComponentSupport
from mixam_sdk.item_specification.models.cover_component import CoverComponent
from mixam_sdk.item_specification.models.custom_size import CustomSize
from mixam_sdk.item_specification.models.dust_jacket_component import DustJacketComponent
from mixam_sdk.item_specification.models.end_papers_component import EndPapersComponent
from mixam_sdk.item_specification.models.envelope_component import EnvelopeComponent
from mixam_sdk.item_specification.models.flat_component import FlatComponent
from mixam_sdk.item_specification.models.folded_component import FoldedComponent
from mixam_sdk.item_specification.models.framed_component import FramedComponent
from mixam_sdk.item_specification.models.sample_pack_component import SamplePackComponent
from mixam_sdk.item_specification.models.shrink_wrap_component import ShrinkWrapComponent
from mixam_sdk.item_specification.models.sticker_component import StickerComponent
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name

ComponentUnion = Union[
    BoundComponent,
    CoverComponent,
    SamplePackComponent,
    DustJacketComponent,
    EndPapersComponent,
    EnvelopeComponent,
    FlatComponent,
    FoldedComponent,
    FramedComponent,
    StickerComponent,
    ShrinkWrapComponent,
]

ComponentTaggedUnion = Annotated[ComponentUnion, Field(discriminator="component_type")]

class ItemSpecification(BaseModel):

    copies: int = Field(
        default=1,
        description="Number of copies to be printed",
    )

    product: Annotated[Product, enum_by_name_or_value(Product), enum_dump_name] = Field(
        default=Product.BROCHURES,
        description="Product type",
    )

    components: List[ComponentTaggedUnion] = Field(
        default_factory=list,
        description="List of components for the specification",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )

    @model_validator(mode="before")
    @classmethod
    def _unwrap(cls, data):
        d = data.get("itemSpecification", data)

        # Frustratingly, There Is No Easy Way To Handle Discriminated Unions In Pydantic So We Have To Do It Manually
        comps = d.get("components")
        if isinstance(comps, list):
            for comp in comps:
                if not isinstance(comp, dict):
                    continue
                tag = comp.pop("component_type", None)
                if tag is None:
                    tag = comp.pop("componentType", None)

                if tag is not None:
                    if isinstance(tag, str):
                        comp["component_type"] = ComponentType[tag]
                    elif isinstance(tag, ComponentType):
                        comp["component_type"] = tag
                    else:
                        raise ValueError(f"Invalid component_type tag: {tag!r}")
        return d

    def get_primary_component(self) -> ComponentSupport:
        for ct in ComponentType:
            for c in self.components:
                if c.component_type == ct:
                    return c
        raise RuntimeError("Primary component not found")

    def has_component(self, component_type: ComponentType) -> bool:
        return any(c.component_type == component_type for c in self.components)

    def get_component(self, component_type: ComponentType):
        matched = [c for c in self.components if c.component_type == component_type]
        if not matched:
            raise RuntimeError(f"Component not found: {component_type}")
        if len(matched) > 1:
            raise RuntimeError(f"There are multiple components of this type: {matched[0]}, {matched[1]}")
        return matched[0]

    def get_component_by_code(self, component_type_code: str):
        matched = [c for c in self.components if c.component_type.name == component_type_code or getattr(c.component_type, "code", None) == component_type_code]
        if not matched:
            raise RuntimeError(f"Component not found by code: {component_type_code}")
        if len(matched) > 1:
            raise RuntimeError(f"There are multiple components of this type: {matched[0]}, {matched[1]}")
        return matched[0]

    def is_bound(self) -> bool:
        return self.get_primary_component().component_type == ComponentType.BOUND

    def is_custom_size(self) -> bool:
        return self.get_primary_component().custom_size is not None

    def supports_spine(self) -> bool:
        primary = self.get_primary_component()
        return isinstance(primary, BoundComponent) and primary.supports_spine()

    def has_foiling(self) -> bool:
        front = any(
            hasattr(c, "foiling") and getattr(c, "foiling").has_foiling()
            for c in self.components
        )
        back = any(
            hasattr(c, "back_foiling") and getattr(c, "back_foiling").has_foiling()
            for c in self.components
        )
        return front or back

    def requires_artwork(self) -> bool:
        return any(getattr(c, "colours", Colours.NONE) != Colours.NONE for c in self.components)


    def _clone(self) -> ItemSpecification:
        return self.model_copy(deep=True)

    def to_size(self, value: int | StandardSize | CustomSize) -> ItemSpecification:
        clone = self._clone()
        if isinstance(value, int):
            for c in clone.components:
                c.configure_size_format(int(value))
        elif isinstance(value, StandardSize):
            for c in clone.components:
                c.configure_size_standard(value)
        else:
            for c in clone.components:
                c.configure_size_custom(value)
        return clone
