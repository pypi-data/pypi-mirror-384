from __future__ import annotations

from mixam_sdk.item_specification.enums.lamination import Lamination
from mixam_sdk.item_specification.enums.pre_drilled_holes import PreDrilledHoles
from mixam_sdk.item_specification.interfaces.component_protocol import (
    TwoSidedComponent as ITwoSidedComponent,
    LaminatedComponent as ILaminatedComponent,
    FoiledComponent as IFoiledComponent,
)
from mixam_sdk.item_specification.models.bound_component import BoundComponent
from mixam_sdk.item_specification.models.component_support import ComponentSupport
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.services.validation_result import ValidationResult
from .base import DefaultComponentValidator


class PrimaryComponentValidator(DefaultComponentValidator):
    """
    Validator that applies rules that are only relevant to the primary component.
    This moves checks that reference the "primaryComponent" from the Java version
    out of the base validator so non-primary components do not get these errors.

    Primary-component rules implemented here:
    - Custom size support (and range check if metadata present in future)
    - Substrate combination validation against product.substrate_types
    - Lamination support against substrate type and weight
    - Orientation enforcement for auto-orientable products
    - Pre-drilled holes availability/options (non-bound only)
    - Foiling dependencies (requires lamination etc.) including back-side for two-sided
    """

    def validate(self, product_metadata: ProductMetadata, item_specification: ItemSpecification, component: ComponentSupport, result: ValidationResult, base_path: str) -> None:
        # Run generic rules that are safe for all components (format, substrate design)
        super().validate(product_metadata, item_specification, component, result, base_path)

        # Primary-only: Validate colours vs product colours metadata (front)
        try:
            allowed_colours = {o.colours.name for o in product_metadata.colours_metadata.colours_options}
            if allowed_colours and component.colours.name not in allowed_colours:
                result.add_error(
                    path=f"{base_path}.colours",
                    message=f"Colours '{component.colours.name}' not available for this product.",
                    code="colours.unavailable",
                    allowed=sorted(list(allowed_colours)),
                )
        except Exception:
            # Ignore metadata errors
            pass

        # Primary-only: Validate back colours for two-sided components
        try:
            if isinstance(component, ITwoSidedComponent):
                allowed_back_colours = {o.colours.name for o in product_metadata.colours_metadata.back_colours_options}
                if allowed_back_colours and component.back_colours.name not in allowed_back_colours:
                    result.add_error(
                        path=f"{base_path}.backColours",
                        message=f"Unsupported back colour '{component.back_colours.name}'.",
                        code="back_colours.unavailable",
                        allowed=sorted(list(allowed_back_colours)),
                    )
        except Exception:
            pass

        # Custom size support: only primary component should be checked strictly
        try:
            if component.has_custom_size() and product_metadata.custom_size_metadata is None:
                result.add_error(
                    path=f"{base_path}.customSize",
                    message="Custom size not supported by this product.",
                    code="custom_size.unsupported",
                )
        except Exception:
            pass

        # Validate substrate combination (type -> colour -> weight) by IDs using primary substrate_types
        try:
            substrate_type_metadata = next((t for t in product_metadata.substrate_types if t.id == component.substrate.type_id), None)
            valid_combo = False
            if substrate_type_metadata is not None:
                substrate_colour_metadata = next((c for c in substrate_type_metadata.substrate_colours if c.id == component.substrate.colour_id), None)
                if substrate_colour_metadata is not None:
                    substrate_weight_metadata = next((w for w in substrate_colour_metadata.weights if w.id == component.substrate.weight_id), None)
                    valid_combo = substrate_weight_metadata is not None
            if not valid_combo:
                result.add_error(
                    path=f"{base_path}.substrate",
                    message=(
                        f"Invalid substrate combination. Type ID: {component.substrate.type_id}, "
                        f"Colour ID: {component.substrate.colour_id}, Weight ID: {component.substrate.weight_id}"
                    ),
                    code="substrate.combo.invalid",
                )
        except Exception:
            pass

        # Orientation rule: auto-orientable products enforce default orientation only (primary only)
        try:
            if product_metadata.auto_orientable and product_metadata.default_orientation is not None:
                if component.orientation != product_metadata.default_orientation:
                    result.add_error(
                        path=f"{base_path}.orientation",
                        message=(
                            f"This product is auto orientable and only supports {product_metadata.default_orientation.name} orientation. "
                            "(Note: Both portrait & landscape artwork files are auto detected and processed accordingly)"
                        ),
                        code="orientation.not_supported",
                        required=product_metadata.default_orientation.name,
                    )
        except Exception:
            pass

        # Pre-drilled holes: only allowed when options exist and not for bound components' special case
        try:
            if not isinstance(component, BoundComponent):
                options = product_metadata.pre_drilled_holes_metadata.pre_drilled_hole_options
                if not options and component.pre_drilled_holes != PreDrilledHoles.NONE:
                    result.add_error(
                        path=f"{base_path}.preDrilledHoles",
                        message="Pre drilled holes are not supported by this product.",
                        code="pre_drilled_holes.unsupported",
                    )
                elif component.pre_drilled_holes != PreDrilledHoles.NONE:
                    allowed = {o.pre_drilled_holes.name for o in options}
                    if component.pre_drilled_holes.name not in allowed:
                        result.add_error(
                            path=f"{base_path}.preDrilledHoles",
                            message="Unsupported Pre Drilled Hole option.",
                            code="pre_drilled_holes.option_invalid",
                            allowed=sorted(list(allowed)),
                        )
        except Exception:
            pass

        # Lamination validations for laminated primary components
        try:
            if isinstance(component, ILaminatedComponent) and component.lamination != Lamination.NONE:
                substrate_type_metadata = next((t for t in product_metadata.substrate_types if t.id == component.substrate.type_id), None)
                if substrate_type_metadata is None or not substrate_type_metadata.allow_lamination:
                    result.add_error(
                        path=f"{base_path}.lamination",
                        message="Unsupported lamination. Specified substrate type does not support lamination.",
                        code="lamination.substrate_type_unsupported",
                    )
                else:
                    try:
                        substrate_colour_metadata = next((c for c in substrate_type_metadata.substrate_colours if c.id == component.substrate.colour_id), None)
                        substrate_weight_metadata = next((w for w in substrate_colour_metadata.weights if w.id == component.substrate.weight_id), None) if substrate_colour_metadata else None
                        if substrate_weight_metadata is not None and not substrate_weight_metadata.supports_lamination:
                            result.add_error(
                                path=f"{base_path}.lamination",
                                message="Lamination is not supported for this substrate weight.",
                                code="lamination.substrate_weight_unsupported",
                            )
                    except Exception:
                        pass
        except Exception:
            pass

        # Foiling validations for primary (front + back if two-sided)
        try:
            if isinstance(component, IFoiledComponent):
                front_has = component.foiling.has_foiling()
                if front_has:
                    if not product_metadata.foiling_metadata.front_foiling:
                        result.add_error(
                            path=f"{base_path}.foiling",
                            message="Foiling is not supported by this product.",
                            code="foiling.unsupported",
                        )
                    else:
                        if isinstance(component, ILaminatedComponent):
                            lam = component.lamination
                            if lam != Lamination.NONE:
                                ok = any(lam in opt.supported_laminations for opt in product_metadata.foiling_metadata.front_foiling)
                                if not ok:
                                    result.add_error(
                                        path=f"{base_path}.foiling",
                                        message="Unsupported foiling option for selected lamination.",
                                        code="foiling.lamination_incompatible",
                                    )
                            else:
                                result.add_error(
                                    path=f"{base_path}.foiling",
                                    message="Unsupported foiling option. Foiling is only available for Laminated Components.",
                                    code="foiling.requires_lamination",
                                )
            if isinstance(component, ITwoSidedComponent):
                # Back lamination rules (SAME_AS_FRONT and availability)
                try:
                    back_lam = component.back_lamination
                    lamination_metadata = product_metadata.lamination_metadata
                    back_lamination_options = lamination_metadata.back_options if lamination_metadata is not None else []
                    # If no back options configured and a back lamination is set, it's unsupported
                    if not back_lamination_options and back_lam != Lamination.NONE:
                        result.add_error(
                            path=f"{base_path}.backLamination",
                            message="This product does not support back lamination.",
                            code="back_lamination.unsupported",
                        )
                    else:
                        # SAME_AS_FRONT behavior if listed among back options
                        same_as_front_available = any(
                            str(opt.lamination).upper() == "SAME_AS_FRONT"
                            for opt in back_lamination_options
                        )
                        if same_as_front_available:
                            # When SAME_AS_FRONT is available, enforce equality if a back lamination is chosen (non-NONE)
                            if back_lam != Lamination.NONE and isinstance(component, ILaminatedComponent) and component.lamination != back_lam:
                                result.add_error(
                                    path=f"{base_path}.backLamination",
                                    message="Back lamination has to be same as front lamination or none.",
                                    code="back_lamination.same_as_front_required",
                                )
                        else:
                            # If SAME_AS_FRONT is not available: back lamination, when set, must be among back options by value
                            if back_lam != Lamination.NONE:
                                allowed_values = {int(opt.value) for opt in back_lamination_options}
                                if allowed_values and back_lam.get_value() not in allowed_values and back_lam.value not in allowed_values:
                                    # Our Lamination enum has get_value(); try both .value and .get_value()
                                    result.add_error(
                                        path=f"{base_path}.backLamination",
                                        message="Unsupported back lamination. This product accepts configured back options only.",
                                        code="back_lamination.option_invalid",
                                        allowed=sorted(list(allowed_values)),
                                    )
                except Exception:
                    pass

                # Back foiling rules
                back_has = component.back_foiling.has_foiling()
                if back_has:
                    if not product_metadata.foiling_metadata.back_foiling:
                        result.add_error(
                            path=f"{base_path}.backFoiling",
                            message="Foiling is not supported by this product on the back side.",
                            code="back_foiling.unsupported",
                        )
                    else:
                        lam = component.back_lamination
                        if lam != Lamination.NONE:
                            ok = any(lam in opt.supported_laminations for opt in product_metadata.foiling_metadata.back_foiling)
                            if not ok:
                                result.add_error(
                                    path=f"{base_path}.backFoiling",
                                    message="Unsupported back foiling option for selected back lamination.",
                                    code="back_foiling.lamination_incompatible",
                                )
                        else:
                            result.add_error(
                                path=f"{base_path}.backFoiling",
                                message="Unsupported foiling option. Back foiling is only available with back lamination.",
                                code="back_foiling.requires_lamination",
                            )
        except Exception:
            pass


__all__ = ["PrimaryComponentValidator"]
