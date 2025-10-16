from __future__ import annotations

from typing import Protocol, runtime_checkable, Tuple, Any, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from mixam_sdk.item_specification.models import Embellishments, CustomSize
    from mixam_sdk.item_specification.models.foiling import Foiling
    from mixam_sdk.item_specification.models.substrate import Substrate
    from mixam_sdk.item_specification.enums.shape import Shape
    from mixam_sdk.item_specification.enums.component_type import ComponentType
    from mixam_sdk.item_specification.enums.standard_size import StandardSize
    from mixam_sdk.item_specification.enums.orientation import Orientation
    from mixam_sdk.item_specification.enums.colours import Colours
    from mixam_sdk.item_specification.enums.pre_drilled_holes import PreDrilledHoles
    from mixam_sdk.item_specification.enums.lamination import Lamination

class Member(BaseModel):
    code: str

class Container(BaseModel):
    code: str

def member_meta(code: str) -> dict[str, Member]:
    return {"member": Member(code=code)}

def container_meta(code: str) -> dict[str, Container]:
    return {"container": Container(code=code)}

@runtime_checkable
class Component(Protocol):
    format: int
    component_type: ComponentType
    standard_size: StandardSize
    custom_size: CustomSize | None
    orientation: Orientation
    substrate: Substrate
    colours: Colours
    pre_drilled_holes: PreDrilledHoles
    embellishments: Embellishments

    def has_back(self) -> bool: ...
    def is_folded(self) -> bool: ...
    def has_custom_size(self) -> bool: ...
    def is_laminated_component(self) -> bool: ...
    def is_two_sided_component(self) -> bool: ...
    def is_foiled_component(self) -> bool: ...
    def is_shaped_component(self) -> bool: ...

@runtime_checkable
class LaminatedComponent(Component, Protocol):
    lamination: Lamination

@runtime_checkable
class FoiledComponent(Component, Protocol):
    foiling: Foiling

@runtime_checkable
class TwoSidedComponent(LaminatedComponent, FoiledComponent, Protocol):
    back_colours: Colours
    back_lamination: Lamination
    back_foiling: Foiling

@runtime_checkable
class ShapedComponent(Component, Protocol):
    shape: Shape

SUBSTRATE_COMPARISON_FORMAT = "%s|%s|%s"

def _enum_key(x: Any) -> str:
    if x is None:
        return ""
    for attr in ("name", "value", "code"):
        if hasattr(x, attr):
            return str(getattr(x, attr))
    return str(x)


def component_comparator_key(c: Component) -> Tuple[str, str, str]:
    primary = _enum_key(getattr(c, "component_type", None))
    cls_name = c.__class__.__name__

    sub = c.substrate
    type_id = getattr(sub, "type_id", "")
    weight_id = getattr(sub, "weight_id", "")
    colour_id = getattr(sub, "colour_id", "")
    triplet = SUBSTRATE_COMPARISON_FORMAT % (type_id, weight_id, colour_id)

    return (primary, cls_name, triplet)