from .validator import ProductItemSpecificationValidator
# Backwards compatibility re-exports for component validators
try:
    from mixam_sdk.metadata.product.models.validators import (
        ComponentValidator,
        DefaultComponentValidator,
        FoldedComponentValidator,
        ShrinkWrapComponentValidator,
        DEFAULT_COMPONENT_VALIDATORS,
    )
except Exception:  # pragma: no cover - if models.validators missing, leave names undefined
    pass

__all__ = [
    "ProductItemSpecificationValidator",
    "ComponentValidator",
    "DefaultComponentValidator",
    "FoldedComponentValidator",
    "ShrinkWrapComponentValidator",
    "DEFAULT_COMPONENT_VALIDATORS",
]
