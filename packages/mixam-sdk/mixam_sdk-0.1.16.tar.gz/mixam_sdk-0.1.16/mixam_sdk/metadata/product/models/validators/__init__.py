from mixam_sdk.item_specification.enums.component_type import ComponentType
from .base import ComponentValidator, DefaultComponentValidator
from .bound import BoundComponentValidator
from .cover import CoverComponentValidator
from .dust_jacket import DustJacketComponentValidator
from .end_papers import EndPapersComponentValidator
from .envelope import EnvelopeComponentValidator
from .flat import FlatComponentValidator
from .folded import FoldedComponentValidator
from .framed import FramedComponentValidator
from .sample_pack import SamplePackComponentValidator
from .shrink_wrap import ShrinkWrapComponentValidator

DEFAULT_COMPONENT_VALIDATORS = {
    ComponentType.FLAT: FlatComponentValidator(),
    ComponentType.SHRINK_WRAP: ShrinkWrapComponentValidator(),
    ComponentType.FOLDED: FoldedComponentValidator(),
    ComponentType.COVER: CoverComponentValidator(),
    ComponentType.BOUND: BoundComponentValidator(),
    ComponentType.END_PAPERS: EndPapersComponentValidator(),
    ComponentType.DUST_JACKET: DustJacketComponentValidator(),
    ComponentType.FRAMED: FramedComponentValidator(),
    ComponentType.SAMPLE_PACK: SamplePackComponentValidator(),
}

# Some deployments may have an ENVELOPE component type; register if present
try:
    DEFAULT_COMPONENT_VALIDATORS[ComponentType.ENVELOPE] = EnvelopeComponentValidator()
except Exception:
    pass

__all__ = [
    "ComponentValidator",
    "DefaultComponentValidator",
    "FoldedComponentValidator",
    "ShrinkWrapComponentValidator",
    "CoverComponentValidator",
    "EnvelopeComponentValidator",
    "BoundComponentValidator",
    "EndPapersComponentValidator",
    "DustJacketComponentValidator",
    "FramedComponentValidator",
    "SamplePackComponentValidator",
    "DEFAULT_COMPONENT_VALIDATORS",
]
