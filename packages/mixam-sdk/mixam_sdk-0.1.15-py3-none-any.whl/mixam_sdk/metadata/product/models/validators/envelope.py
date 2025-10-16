from __future__ import annotations

from mixam_sdk.item_specification.enums.lamination import Lamination
from mixam_sdk.item_specification.interfaces.component_protocol import LaminatedComponent as ILaminatedComponent
from mixam_sdk.item_specification.models.envelope_component import EnvelopeComponent
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.services.validation_result import ValidationResult
from .base import DefaultComponentValidator


class EnvelopeComponentValidator(DefaultComponentValidator):
    def validate(self, product_metadata: ProductMetadata, item_specification: ItemSpecification, envelope_component: EnvelopeComponent, result: ValidationResult, base_path: str) -> None:
        # Ensure correct component type
        if not isinstance(envelope_component, EnvelopeComponent):
            result.add_error(
                path=base_path,
                message="Invalid component type for EnvelopeComponentValidator: expected EnvelopeComponent",
                code="validator.component.type_mismatch",
                expected="EnvelopeComponent",
            )
            return
        super().validate(product_metadata, item_specification, envelope_component, result, base_path)
        # Validate using envelope substrate metadata
        try:
            envelope_substrate_type_metadata = next((t for t in product_metadata.envelope_substrate_types if t.id == envelope_component.substrate.type_id), None)
            valid_combo = False
            if envelope_substrate_type_metadata is not None:
                envelope_substrate_colour_metadata = next((c for c in envelope_substrate_type_metadata.substrate_colours if c.id == envelope_component.substrate.colour_id), None)
                if envelope_substrate_colour_metadata is not None:
                    envelope_substrate_weight_metadata = next((w for w in envelope_substrate_colour_metadata.weights if w.id == envelope_component.substrate.weight_id), None)
                    valid_combo = envelope_substrate_weight_metadata is not None
            if not valid_combo:
                result.add_error(
                    path=f"{base_path}.substrate",
                    message=(
                        f"Invalid substrate combination for envelope. Type ID: {envelope_component.substrate.type_id}, "
                        f"Colour ID: {envelope_component.substrate.colour_id}, Weight ID: {envelope_component.substrate.weight_id}"
                    ),
                    code="substrate.combo.invalid.envelope",
                )
        except Exception:
            pass
        # Check lamination against envelope substrate settings
        try:
            if isinstance(envelope_component, ILaminatedComponent) and envelope_component.lamination != Lamination.NONE:
                envelope_substrate_type_metadata = next((t for t in product_metadata.envelope_substrate_types if t.id == envelope_component.substrate.type_id), None)
                if envelope_substrate_type_metadata is None or not envelope_substrate_type_metadata.allow_lamination:
                    result.add_error(
                        path=f"{base_path}.lamination",
                        message="Unsupported lamination for envelope. Specified substrate type does not support lamination.",
                        code="lamination.substrate_type_unsupported.envelope",
                    )
                else:
                    try:
                        envelope_substrate_colour_metadata = next((c for c in envelope_substrate_type_metadata.substrate_colours if c.id == envelope_component.substrate.colour_id), None)
                        envelope_substrate_weight_metadata = next((w for w in envelope_substrate_colour_metadata.weights if w.id == envelope_component.substrate.weight_id), None) if envelope_substrate_colour_metadata else None
                        if envelope_substrate_weight_metadata is not None and not envelope_substrate_weight_metadata.supports_lamination:
                            result.add_error(
                                path=f"{base_path}.lamination",
                                message="Lamination is not supported for this envelope substrate weight.",
                                code="lamination.substrate_weight_unsupported.envelope",
                            )
                    except Exception:
                        pass
        except Exception:
            pass


__all__ = ["EnvelopeComponentValidator"]
