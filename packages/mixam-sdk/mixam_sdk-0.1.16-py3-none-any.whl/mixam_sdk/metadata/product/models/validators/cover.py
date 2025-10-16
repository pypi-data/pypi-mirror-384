from __future__ import annotations

from mixam_sdk.item_specification.enums.lamination import Lamination
from mixam_sdk.item_specification.interfaces.component_protocol import LaminatedComponent as ILaminatedComponent
from mixam_sdk.item_specification.models.cover_component import CoverComponent
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.models.validators.utils import select_binding_type_option_for_item_specification
from mixam_sdk.metadata.product.services.validation_result import ValidationResult
from .base import DefaultComponentValidator


class CoverComponentValidator(DefaultComponentValidator):
    def validate(self, product_metadata: ProductMetadata, item_specification: ItemSpecification, cover_component: CoverComponent, result: ValidationResult, base_path: str) -> None:
        # Ensure correct component type
        if not isinstance(cover_component, CoverComponent):
            result.add_error(
                path=base_path,
                message="Invalid component type for CoverComponentValidator: expected CoverComponent",
                code="validator.component.type_mismatch",
                expected="CoverComponent",
            )
            return
        # Run base checks
        super().validate(product_metadata, item_specification, cover_component, result, base_path)
        # Check substrate combo
        try:
            cover_substrate_type_metadata = next((t for t in product_metadata.cover_substrate_types if t.id == cover_component.substrate.type_id), None)
            valid_combo = False
            if cover_substrate_type_metadata is not None:
                cover_substrate_colour_metadata = next((c for c in cover_substrate_type_metadata.substrate_colours if c.id == cover_component.substrate.colour_id), None)
                if cover_substrate_colour_metadata is not None:
                    cover_substrate_weight_metadata = next((w for w in cover_substrate_colour_metadata.weights if w.id == cover_component.substrate.weight_id), None)
                    valid_combo = cover_substrate_weight_metadata is not None
            if not valid_combo:
                result.add_error(
                    path=f"{base_path}.substrate",
                    message=(
                        f"Invalid substrate combination for cover. Type ID: {cover_component.substrate.type_id}, "
                        f"Colour ID: {cover_component.substrate.colour_id}, Weight ID: {cover_component.substrate.weight_id}"
                    ),
                    code="substrate.combo.invalid.cover",
                )
        except Exception:
            pass
        # Check lamination against cover substrate settings
        try:
            if isinstance(cover_component, ILaminatedComponent) and cover_component.lamination != Lamination.NONE:
                cover_substrate_type_metadata = next((t for t in product_metadata.cover_substrate_types if t.id == cover_component.substrate.type_id), None)
                if cover_substrate_type_metadata is None or not cover_substrate_type_metadata.allow_lamination:
                    result.add_error(
                        path=f"{base_path}.lamination",
                        message="Unsupported lamination for cover. Specified substrate type does not support lamination.",
                        code="lamination.substrate_type_unsupported.cover",
                    )
                else:
                    try:
                        cover_substrate_colour_metadata = next((c for c in cover_substrate_type_metadata.substrate_colours if c.id == cover_component.substrate.colour_id), None)
                        cover_substrate_weight_metadata = next((w for w in cover_substrate_colour_metadata.weights if w.id == cover_component.substrate.weight_id), None) if cover_substrate_colour_metadata else None
                        if cover_substrate_weight_metadata is not None and not cover_substrate_weight_metadata.supports_lamination:
                            result.add_error(
                                path=f"{base_path}.lamination",
                                message="Lamination is not supported for this cover substrate weight.",
                                code="lamination.substrate_weight_unsupported.cover",
                            )
                    except Exception:
                        pass
        except Exception:
            pass
        # Colours depend on binding option
        try:
            match = select_binding_type_option_for_item_specification(item_specification, product_metadata.cover_substrate_types, product_metadata.bound_metadata)
            binding_type_option = match.binding_type_option
            if binding_type_option is not None:
                # Outer colours
                outer_options = binding_type_option.separate_cover_outer_colours_options
                allowed_outer = {o.colours.name for o in outer_options}
                if allowed_outer and cover_component.colours.name not in allowed_outer:
                    result.add_error(
                        path=f"{base_path}.colours",
                        message="Unsupported colour (outer).",
                        code="cover.outer_colours.unavailable",
                        allowed=sorted(list(allowed_outer)),
                    )
                # Inner colours with SAME_AS_FRONT handling
                inner_options = binding_type_option.separate_cover_inner_colours_options
                same_as_front = any(o.same_as_front for o in inner_options)
                if same_as_front:
                    if cover_component.back_colours.name not in {cover_component.colours.name, "NONE"}:
                        result.add_error(
                            path=f"{base_path}.backColours",
                            message="Unsupported back colour (inner). Must match front or be NONE",
                            code="cover.inner_colours.same_as_front_required",
                        )
                else:
                    allowed_inner = {o.colours.name for o in inner_options}
                    if allowed_inner and cover_component.back_colours.name not in allowed_inner:
                        result.add_error(
                            path=f"{base_path}.backColours",
                            message="Unsupported back colour (inner).",
                            code="cover.inner_colours.unavailable",
                            allowed=sorted(list(allowed_inner)),
                        )
        except Exception:
            # Ignore metadata issues
            pass


__all__ = ["CoverComponentValidator"]
