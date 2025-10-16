from __future__ import annotations

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.enums.flap_width import FlapWidth
from mixam_sdk.item_specification.enums.lamination import Lamination
from mixam_sdk.item_specification.models.dust_jacket_component import DustJacketComponent
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.models.validators.utils import select_binding_type_option_for_item_specification
from mixam_sdk.metadata.product.services.validation_result import ValidationResult
from .base import DefaultComponentValidator


class DustJacketComponentValidator(DefaultComponentValidator):
    def validate(self, product_metadata: ProductMetadata, item_specification: ItemSpecification, dust_jacket_component: DustJacketComponent, result: ValidationResult, base_path: str) -> None:

        # Ensure correct component type
        if not isinstance(dust_jacket_component, DustJacketComponent):
            result.add_error(
                path=base_path,
                message="Invalid component type for DustJacketComponentValidator: expected DustJacketComponent",
                code="validator.component.type_mismatch",
                expected="DustJacketComponent",
            )
            return
        super().validate(product_metadata, item_specification, dust_jacket_component, result, base_path)

        try:
            try:
                if item_specification.has_component(ComponentType.BOUND):
                    match = select_binding_type_option_for_item_specification(item_specification, product_metadata.cover_substrate_types, product_metadata.bound_metadata)
                    binding_type_option = match.binding_type_option
                    if binding_type_option is not None and not binding_type_option.supports_dust_jacket:
                        result.add_error(
                            path=f"{base_path}",
                            message="Dust Jackets are not supported by this binding type",
                            code="bound.dust_jacket.unsupported",
                        )
            except Exception:
                pass

            # Colours allowed for dust jacket
            try:
                allowed_dj_colours = {o.colours.name for o in product_metadata.colours_metadata.jacket_colours_options}
                if allowed_dj_colours and dust_jacket_component.colours.name not in allowed_dj_colours:
                    result.add_error(
                        path=f"{base_path}.colours",
                        message="Unsupported colour.",
                        code="dust_jacket.colours.unavailable",
                        allowed=sorted(list(allowed_dj_colours)),
                    )
            except Exception:
                pass

            # Lamination options for dust jacket
            try:
                lamination_metadata = product_metadata.lamination_metadata
                dust_jacket_options = lamination_metadata.dust_jacket_options if lamination_metadata is not None else []
                if not dust_jacket_options and dust_jacket_component.lamination != Lamination.NONE:
                    result.add_error(
                        path=f"{base_path}.lamination",
                        message="This product does not support lamination",
                        code="dust_jacket.lamination.unsupported",
                    )
                elif dust_jacket_component.lamination != Lamination.NONE:
                    allowed_values = {int(opt.value) for opt in dust_jacket_options}
                    if allowed_values and dust_jacket_component.lamination.get_value() not in allowed_values and dust_jacket_component.lamination.value not in allowed_values:
                        result.add_error(
                            path=f"{base_path}.lamination",
                            message="Unsupported lamination. This product accepts configured dust jacket laminations",
                            code="dust_jacket.lamination.option_invalid",
                            allowed=sorted(list(allowed_values)),
                        )
            except Exception:
                pass

            # Foiling support for dust jacket
            try:
                if dust_jacket_component.foiling.has_foiling() and not product_metadata.foiling_metadata.dust_jacket_foiling:
                    result.add_error(
                        path=f"{base_path}.foiling",
                        message="Foiling is not supported by this product",
                        code="dust_jacket.foiling.unsupported",
                    )
            except Exception:
                pass

            # If flapWidth is CUSTOM then customFlapWidth must be provided
            if dust_jacket_component.flap_width == FlapWidth.CUSTOM:
                if dust_jacket_component.custom_flap_width is None:
                    result.add_error(
                        path=f"{base_path}.customFlapWidth",
                        message="CustomFlapWidth must be set when FlapWidth is CUSTOM",
                        code="dust_jacket.custom_flap_width.required",
                    )
        except Exception:
            # Ignore metadata issues
            pass


__all__ = ["DustJacketComponentValidator"]
