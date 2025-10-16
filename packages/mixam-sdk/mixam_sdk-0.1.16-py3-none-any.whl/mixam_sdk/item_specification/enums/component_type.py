from __future__ import annotations

from enum import Enum
from importlib import import_module
from typing import Tuple, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from mixam_sdk.item_specification.interfaces.component_protocol import Component

class ComponentType(Enum):

    FLAT = "FLAT"
    FOLDED = "FOLDED"
    BOUND = "BOUND"
    COVER = "COVER"
    END_PAPERS = "END_PAPERS"
    DUST_JACKET = "DUST_JACKET"
    FRAMED = "FRAMED"
    STICKER = "STICKER"
    ENVELOPE = "ENVELOPE"
    SHRINK_WRAP = "SHRINK_WRAP"
    SAMPLE_PACK = "SAMPLE_PACK"

    def get_code(self) -> str:
        return COMPONENT_META[self][0]

    def get_dotted_path(self) -> str:
        return COMPONENT_META[self][1]

    def get_component_class(self) -> Type[Component]:
        dotted = self.get_dotted_path()
        module_name, _, class_name = dotted.partition(":")
        if not module_name or not class_name:
            raise RuntimeError(f"Invalid component dotted path: {dotted!r}")
        module = import_module(module_name)
        cls = getattr(module, class_name)
        return cls

    @staticmethod
    def for_code(code: str) -> ComponentType:
        for ct, (c, _) in COMPONENT_META.items():
            if c == code:
                return ct
        raise ValueError(f"Unrecognized ComponentType code: {code}")

COMPONENT_META: dict[ComponentType, Tuple[str, str]] = {
    ComponentType.FLAT: ("ft", "mixam_sdk.item_specification.models.flat_component:FlatComponent"),
    ComponentType.FOLDED: ("fd", "mixam_sdk.item_specification.models.folded_component:FoldedComponent"),
    ComponentType.BOUND: ("bd", "mixam_sdk.item_specification.models.bound_component:BoundComponent"),
    ComponentType.COVER: ("cr", "mixam_sdk.item_specification.models.cover_component:CoverComponent"),
    ComponentType.END_PAPERS: ("ep", "mixam_sdk.item_specification.models.end_papers_component:EndPapersComponent"),
    ComponentType.DUST_JACKET: ("dj", "mixam_sdk.item_specification.models.dust_jacket_component:DustJacketComponent"),
    ComponentType.FRAMED: ("fr", "mixam_sdk.item_specification.models.framed_component:FramedComponent"),
    ComponentType.STICKER: ("st", "mixam_sdk.item_specification.models.sticker_component:StickerComponent"),
    ComponentType.ENVELOPE: ("en", "mixam_sdk.item_specification.models.envelope_component:EnvelopeComponent"),
    ComponentType.SHRINK_WRAP: ("sw", "mixam_sdk.item_specification.models.shrink_wrap_component:ShrinkWrapComponent"),
    ComponentType.SAMPLE_PACK: ("sp", "mixam_sdk.item_specification.models.sample_pack_component:SamplePackComponent"),
}