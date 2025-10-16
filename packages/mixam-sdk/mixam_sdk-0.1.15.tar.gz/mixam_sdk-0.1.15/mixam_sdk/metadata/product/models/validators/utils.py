from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.enums.head_and_tail_bands import HeadAndTailBands
from mixam_sdk.item_specification.enums.pre_drilled_holes import PreDrilledHoles
from mixam_sdk.item_specification.enums.ribbon_colour import RibbonColour
from mixam_sdk.item_specification.models.bound_component import BoundComponent
from mixam_sdk.item_specification.models.cover_component import CoverComponent
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.metadata.product.enums.trilean import Trilean
from mixam_sdk.metadata.product.models.binding_type_option import BindingTypeOption
from mixam_sdk.metadata.product.models.bound_metadata import BoundMetadata
from mixam_sdk.metadata.product.models.substrate_type_metadata import SubstrateTypeMetadata
from mixam_sdk.metadata.product.services.validation_result import ValidationMessage


@dataclass(frozen=True)
class BindingTypeOptionMatch:
    binding_type_option: Optional[BindingTypeOption]
    errors: List[ValidationMessage]




def _validate_binding_type_option_against_item_spec(option: BindingTypeOption,
                                                    spec: ItemSpecification,
                                                    cover_substrate_types: List[SubstrateTypeMetadata]) -> List[ValidationMessage]:
    violations: List[ValidationMessage] = []
    bound: BoundComponent = spec.get_component(ComponentType.BOUND)

    # Sewing support
    if bound.binding.sewn and option.sewing == Trilean.UNAVAILABLE:
        violations.append(ValidationMessage(
            path="boundComponent.binding.sewn",
            message="Sewing is not available for this binding type",
            code="bound.sewing.unsupported",
        ))
    # Ribbons
    if not option.supports_ribbons and bound.ribbon_colour != RibbonColour.NONE:
        violations.append(ValidationMessage(
            path="boundComponent.ribbonColour",
            message="Ribbons are not supported by this binding type",
            code="bound.ribbon.unsupported",
        ))
    # Head & tail bands
    if not option.supports_head_and_tail_bands and bound.binding.head_and_tail_bands != HeadAndTailBands.NONE:
        violations.append(ValidationMessage(
            path="boundComponent.binding.headAndTailBands",
            message="Head & Tail Bands are not supported by this binding type",
            code="bound.head_and_tail_bands.unsupported",
        ))
    # Pre-drilled holes policy
    if option.pre_drilled_holes == Trilean.REQUIRED and bound.pre_drilled_holes == PreDrilledHoles.NONE:
        violations.append(ValidationMessage(
            path="boundComponent.preDrilledHoles",
            message="Pre-drilled holes are required for this binding type",
            code="bound.pre_drilled_holes.required",
        ))
    elif option.pre_drilled_holes == Trilean.UNAVAILABLE and bound.pre_drilled_holes != PreDrilledHoles.NONE:
        violations.append(ValidationMessage(
            path="boundComponent.preDrilledHoles",
            message="Pre-drilled holes are not available for this binding type",
            code="bound.pre_drilled_holes.unavailable",
        ))

    # Binding colour options
    if option.colour_options:
        has_colour = any(co.binding_colour == bound.binding.colour for co in option.colour_options)
        if not has_colour:
            violations.append(ValidationMessage(
                path="boundComponent.binding.colour",
                message="Unsupported Binding Colour for this binding type",
                code="bound.binding_colour.unavailable",
                extra={"allowed": [co.binding_colour.name for co in option.colour_options]},
            ))
    else:
        # Default/none behaviour: only BLACK is acceptable
        if bound.binding.colour.name != "BLACK":
            violations.append(ValidationMessage(
                path="boundComponent.binding.colour",
                message="Binding colour is not supported by this binding type",
                code="bound.binding_colour.unsupported",
            ))

    # Cover requirement availability
    if option.separate_cover == Trilean.REQUIRED and not spec.has_component(ComponentType.COVER):
        violations.append(ValidationMessage(
            path="coverComponent",
            message="A cover component is required for this product",
            code="bound.cover.required",
        ))
    elif option.separate_cover == Trilean.UNAVAILABLE and spec.has_component(ComponentType.COVER):
        violations.append(ValidationMessage(
            path="coverComponent",
            message="Covers are not supported by this product",
            code="bound.cover.unavailable",
        ))

    if spec.has_component(ComponentType.COVER):
        cover: CoverComponent = spec.get_component(ComponentType.COVER)
        is_valid_substrate = True
        if option.required_substrate is not None:
            is_valid_substrate = (
                option.required_substrate.type_id == cover.substrate.type_id and
                option.required_substrate.colour_id == cover.substrate.colour_id and
                option.required_substrate.weight_id == cover.substrate.weight_id
            )
        else:
            st = next((t for t in cover_substrate_types if t.id == cover.substrate.type_id), None)
            if st is None:
                is_valid_substrate = False
            else:
                sc = next((c for c in st.substrate_colours if c.id == cover.substrate.colour_id), None)
                if sc is None:
                    is_valid_substrate = False
                else:
                    sw = next((w for w in sc.weights if w.id == cover.substrate.weight_id), None)
                    is_valid_substrate = sw is not None
        if not is_valid_substrate:
            violations.append(ValidationMessage(
                path="coverComponent.substrate",
                message=(
                    f"Invalid substrate combination. Type ID: {cover.substrate.type_id}, "
                    f"Colour ID: {cover.substrate.colour_id}, Weight ID: {cover.substrate.weight_id}"
                ),
                code="cover.substrate.combo.invalid",
            ))

    from mixam_sdk.item_specification.enums.component_type import ComponentType as _CT
    if not option.supports_end_papers and spec.has_component(_CT.END_PAPERS):
        violations.append(ValidationMessage(
            path="endPaperComponent",
            message="End papers are not supported by this binding type",
            code="bound.end_papers.unsupported",
        ))
    if option.supports_end_papers and not spec.has_component(_CT.END_PAPERS):
        violations.append(ValidationMessage(
            path="endPaperComponent",
            message="EndPaper component is missing",
            code="bound.end_papers.missing",
        ))

    if not option.supports_dust_jacket and spec.has_component(_CT.DUST_JACKET):
        violations.append(ValidationMessage(
            path="dustJacketComponent",
            message="Dust Jackets are not supported by this binding type",
            code="bound.dust_jacket.unsupported",
        ))

    return violations


def select_binding_type_option_for_item_specification(spec: ItemSpecification,
                                                       cover_substrate_types: List[SubstrateTypeMetadata],
                                                       bound_metadata: BoundMetadata) -> BindingTypeOptionMatch:
    bound: BoundComponent = spec.get_component(ComponentType.BOUND)

    fewest_violations: List[ValidationMessage] | None = None
    selected: Optional[BindingTypeOption] = None

    for option in bound_metadata.binding_type_options:
        # Must match on binding type first
        if option.binding_type != bound.binding.type:
            continue
        violations = _validate_binding_type_option_against_item_spec(option, spec, cover_substrate_types)
        if not violations:
            selected = option
            fewest_violations = []
            break
        if fewest_violations is None or len(violations) < len(fewest_violations):
            fewest_violations = violations

    return BindingTypeOptionMatch(binding_type_option=selected, errors=fewest_violations or [])
