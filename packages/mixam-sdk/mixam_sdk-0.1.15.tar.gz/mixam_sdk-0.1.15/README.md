# Mixam Python SDK

Mixam SDK is a lightweight Python library that helps you build, validate, serialize, and parse print Item Specifications used by Mixam. It provides:

- Core data models and enums to represent product specifications (components, substrates, bindings, sizes, etc.).
- A Universal Key system to serialize an ItemSpecification to a compact string and parse it back reliably.

## Installation

- Via pip:

```bash
pip install mixam-sdk
```

- Via Poetry:

```bash
poetry add mixam-sdk
```

Python 3.12+ is required (see `pyproject.toml`).

## Developers

- Run tests:

```bash
pytest -q
```

- Local install for development:

```bash
poetry install
poetry run pytest -q
```

See the Development section below for more details.

## Quick Start

Below are minimal examples showing how to work with Item Specifications and the Universal Key.

### Create an ItemSpecification and build a Universal Key

```python
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.item_specification.enums.product import Product
from mixam_sdk.item_specification.models.flat_component import FlatComponent
from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.universal_key.models.key_builder import KeyBuilder

# Build a simple spec with one flat component
item = ItemSpecification()
item.copies = 250
item.product = Product.POSTERS

# Create a simple flat component
comp = FlatComponent()
comp.component_type = ComponentType.FLAT
# ... populate additional fields supported by FlatComponent as needed ...

item.components.append(comp)

# Build a Universal Key string
key = KeyBuilder().build(item)
print(key)
```

### Parse a Universal Key back into an ItemSpecification

```python
from mixam_sdk.universal_key.models.key_parser import KeyParser

parser = KeyParser()
# Provide a Universal Key string (from earlier build step or an external source)
some_key = "250~10-ft{...}"
parsed = parser.parse(some_key)

print(parsed.copies)
print(parsed.product)
print([c.component_type for c in parsed.components])
```

If the key does not match the expected format, `KeyParser.parse` raises a `ValueError` or `RuntimeError` indicating the issue.

## What is a Universal Key?

A Universal Key is a compact, validated string representation of an `ItemSpecification`.

- Format (high level):
  - `copies~productId-<component>{<memberTokens>}-<component>{...}`
- Example: `250~10-ft{...}-bd{...}`
- Keys are validated using a strict regex to ensure correctness before parsing.

The SDK provides:

- `KeyBuilder` to generate keys from `ItemSpecification` objects.
- `KeyParser` to parse keys back into `ItemSpecification` objects.

## Main Concepts

- Enums: Found under `mixam_sdk/item_specification/enums`, they define allowed values for products, sizes, colours, laminations, bindings, etc.
- Models: Under `mixam_sdk/item_specification/models`, they represent components such as flat, folded, cover, bound components, and more, as well as the root `ItemSpecification`.
- Interfaces/Support: Internal helpers for ordering components and mapping model fields to the Universal Key token format.

Explore the `tests/` folder for concrete usage patterns and expected behaviours:

- `tests/test_universal_key.py`
- `tests/test_item_specification_deserialization.py`

## Product Metadata and Validation

This SDK models Mixam Product Metadata and provides a validation service to check that a given `ItemSpecification` complies with that metadata.

Important scope notes:
- The validator service is the recommended way to validate a full ItemSpecification. Use `ProductItemSpecificationValidator` for end-to-end validation.
- For advanced implementations, you may validate only a specific component type using its corresponding component validator (component-based validation). See the section below for details.
- The SDK itself does not fetch product metadata; you must retrieve it from the Mixam Public API and pass it to the SDK.
- The SDK focuses on modelling the metadata objects and validating specifications against them.

Obtaining Product Metadata (Mixam Public API):
- Documentation: https://mixam.co.uk/documentation/api/public#openapi
- Endpoint to get product metadata for a specific product and sub-product (provide `productId`, `subProductId`, and `quoteType`, usually `QUOTE`):
  - Example: https://mixam.co.uk/api/public/products/metadata/1/0?quoteType=QUOTE

What is Product Metadata?
- A structured definition of the options and constraints for a specific product (allowed components, sizes, substrates, laminations, page ranges, etc.).
- Represented by `mixam_sdk.metadata.product.models.product_metadata.ProductMetadata` (a Pydantic model).

Validation at a glance:
- You validate an `ItemSpecification` against a `ProductMetadata` using `ProductItemSpecificationValidator`.
- Validation returns a `ValidationResult` containing a list of violations (errors) and optionally warnings.
- Validation is not fail-fast; it accumulates all violations so you can report everything in one pass.
- Each violation includes a machine-readable `code`, a human `message`, a `path` to the offending field/component, and optional `allowed` or other context.

End-to-end example (fetch metadata, build spec in code, validate via service):

```python
import json
from urllib.request import urlopen

from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.item_specification.models.flat_component import FlatComponent
from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.services.validator import ProductItemSpecificationValidator

# 1) Fetch Product Metadata from Mixam Public API (replace IDs as needed)
product_id = 1
sub_product_id = 0
quote_type = "QUOTE"
url = f"https://mixam.co.uk/api/public/products/metadata/{product_id}/{sub_product_id}?quoteType={quote_type}"
with urlopen(url, timeout=20) as resp:
    pm_json = resp.read().decode("utf-8")
pm = ProductMetadata.model_validate_json(pm_json)

# 2) Build an ItemSpecification in code (example: simple flat/poster-style component)
spec = ItemSpecification()
spec.copies = 100

comp = FlatComponent()
comp.component_type = ComponentType.FLAT
# Populate additional fields that your product requires (size, substrate, colours, etc.)
# e.g. comp.standard_size = ... ; comp.substrate = ... ; comp.colours = ...

spec.components.append(comp)

# 3) Validate via the service (the only supported entry point)
validator = ProductItemSpecificationValidator()
result = validator.validate(pm, spec)

# 4) Inspect result
if result.is_valid():
    print("Spec is valid for this product")
else:
    for err in result.errors:
        print(f"{err.path}: {err.code} - {err.message}")
        if err.allowed:
            print(f"  allowed: {err.allowed}")
```

Notes:
- Do not call `metadata.validate(spec)` directly; use `ProductItemSpecificationValidator`.
- Ensure the ItemSpecification fields you set correspond to options allowed by the fetched metadata.

Key classes:
- ProductMetadata: Pydantic model for the product's rules and options.
- ProductItemSpecificationValidator: Service that validates an `ItemSpecification` against `ProductMetadata`.
- ValidationResult and ValidationMessage: Returned by validation; contains `errors`, `warnings`, and helpers like `.is_valid()` and `.humanize()`.

See also:
- Component validators under `mixam_sdk/metadata/product/models/validators/` for component-specific rules (e.g., cover, bound, envelope).
- Tests that exercise validation: `tests/test_product_item_spec_validation.py`, product-specific tests like posters/booklets, etc.

### Example: Validate a 100 A5 Portrait Stapled Booklet (32 pages)

The following JSON spec (simplified) describes what we want to validate:

- 100 Booklets
- Size: A5 (148 mm x 210 mm) - Portrait
- Stapled, Full-colour printing, 32 pages, 130gsm Silk
- Cover: Full-colour printing (front and back), 250gsm Silk

And here is the equivalent ItemSpecification built in code and validated via the service:

```python
from urllib.request import urlopen

from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.item_specification.enums.product import Product
from mixam_sdk.item_specification.models.bound_component import BoundComponent
from mixam_sdk.item_specification.models.cover_component import CoverComponent
from mixam_sdk.item_specification.models.substrate import Substrate
from mixam_sdk.item_specification.models.binding import Binding
from mixam_sdk.item_specification.enums.orientation import Orientation
from mixam_sdk.item_specification.enums.colours import Colours
from mixam_sdk.item_specification.enums.standard_size import StandardSize
from mixam_sdk.item_specification.enums.lamination import Lamination
from mixam_sdk.item_specification.enums.ribbon_colour import RibbonColour
from mixam_sdk.item_specification.enums.binding_type import BindingType
from mixam_sdk.item_specification.enums.binding_edge import BindingEdge
from mixam_sdk.item_specification.enums.substrate_design import SubstrateDesign
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.services.validator import ProductItemSpecificationValidator

# 1) Fetch metadata for brochures (replace IDs for your locale/product if needed)
product_id = 1
sub_product_id = 0
quote_type = "QUOTE"
url = f"https://mixam.co.uk/api/public/products/metadata/{product_id}/{sub_product_id}?quoteType={quote_type}"
with urlopen(url, timeout=20) as resp:
    pm_json = resp.read().decode("utf-8")
pm = ProductMetadata.model_validate_json(pm_json)

# 2) Build the ItemSpecification matching the provided spec
spec = ItemSpecification()
spec.copies = 100
spec.product = Product.BROCHURES

# Primary content (text) block: BOUND component
inner = BoundComponent()
inner.format = 5  # A5
inner.orientation = Orientation.PORTRAIT
inner.colours = Colours.PROCESS
inner.substrate = Substrate(typeId=1, weightId=3, colourId=0, design=SubstrateDesign.NONE)
inner.pages = 32
inner.lamination = Lamination.NONE
inner.binding = Binding(type=BindingType.STAPLED, sewn=False, edge=BindingEdge.LEFT_RIGHT)
inner.ribbon_colour = RibbonColour.NONE

# Cover block: COVER component (front and back)
cover = CoverComponent()
cover.format = 5  # A5
cover.orientation = Orientation.PORTRAIT
cover.colours = Colours.PROCESS
cover.substrate = Substrate(typeId=1, weightId=7, colourId=0, design=SubstrateDesign.NONE)
cover.lamination = Lamination.NONE
cover.back_colours = Colours.PROCESS
cover.back_lamination = Lamination.NONE

spec.components = [inner, cover]

# 3) Validate via the service
validator = ProductItemSpecificationValidator()
result = validator.validate(pm, spec)

if result.is_valid():
    print("Spec is valid for this product")
else:
    for err in result.errors:
        print(f"{err.path}: {err.code} - {err.message}")
        if err.allowed:
            print(f"  allowed: {err.allowed}")
```

Notes:
- Substrate IDs (typeId/weightId/colourId) must match what the fetched Product Metadata allows for the chosen product and sub-product.

## Error Handling

- `KeyParser.parse(key)` validates input and raises a `ValueError` for invalid format and a `RuntimeError` for parsing failures.
- When building keys, ensure your components are populated with required fields; otherwise the builder may not emit expected tokens.

## Development

- Run tests:

```bash
pytest -q
```

- Local install for development:

```bash
poetry install
poetry run pytest -q
```

## Versioning

The package follows semantic versioning where possible. See `pyproject.toml` for the current version.

## License

Copyright (c) Mixam.

See the repository for license terms or contact developer@mixam.com.

## Examples (from tests)

Below are full examples taken directly from the test suite to illustrate the exact formats.

- Universal Key example (Booklet):

```
10~1-bd{4bt-5c-4f-200p-1st-3sw}-cr{5c-5c+-4f-4l-1st-7sw}
```

- Matching ItemSpecification JSON example (as used in tests):

```json
{
  "itemSpecification": {
    "copies": 10,
    "product": "BROCHURES",
    "components": [
      {
        "componentType": "BOUND",
        "format": 4,
        "standardSize": "NONE",
        "orientation": "PORTRAIT",
        "colours": "PROCESS",
        "substrate": {
          "typeId": 1,
          "weightId": 3,
          "colourId": 0
        },
        "pages": 200,
        "lamination": "NONE",
        "binding": {
          "type": "PUR"
        }
      },
      {
        "componentType": "COVER",
        "format": 4,
        "standardSize": "NONE",
        "orientation": "PORTRAIT",
        "colours": "PROCESS",
        "substrate": {
          "typeId": 1,
          "weightId": 7,
          "colourId": 0
        },
        "lamination": "GLOSS",
        "backColours": "PROCESS",
        "backLamination": "NONE"
      }
    ]
  }
}
```

## Links

- Source: https://github.com/mixam-platform/mixam-python-sdk
- Mixam: https://mixam.com


## Component-based validation (advanced)

### Validate just Cover components with the Cover validator (component-only)

While it is recommended to use the validator service to validate the entire Item Specification, the metadata validation system is component-based under the hood. You can shortcut the flow and validate only a specific component type using its corresponding component validator. This can be useful when composing a spec in a component-by-component manner (e.g., with an AI tool) and you only want to validate the component you just changed.

Below is a fully self-contained example that validates only COVER components using the CoverComponentValidator:

```python
from urllib.request import urlopen

from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.item_specification.models.cover_component import CoverComponent
from mixam_sdk.item_specification.models.substrate import Substrate
from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.enums.colours import Colours
from mixam_sdk.item_specification.enums.orientation import Orientation
from mixam_sdk.item_specification.enums.standard_size import StandardSize
from mixam_sdk.item_specification.enums.substrate_design import SubstrateDesign
from mixam_sdk.item_specification.enums.product import Product
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.models.validators.cover import CoverComponentValidator
from mixam_sdk.metadata.product.services.validation_result import ValidationResult

# 1) Fetch Product Metadata for a brochures-like product (adjust IDs for your target product)
product_id = 1
sub_product_id = 0
quote_type = "QUOTE"
url = f"https://mixam.co.uk/api/public/products/metadata/{product_id}/{sub_product_id}?quoteType={quote_type}"
with urlopen(url, timeout=20) as resp:
    pm_json = resp.read().decode("utf-8")
pm = ProductMetadata.model_validate_json(pm_json)

# 2) Build an ItemSpecification with a COVER component (minimal example)
spec = ItemSpecification()
spec.copies = 100
spec.product = Product.BROCHURES

cover = CoverComponent()
cover.format = 5
cover.orientation = Orientation.PORTRAIT
cover.colours = Colours.PROCESS
cover.substrate = Substrate(typeId=1, weightId=7, colourId=0, design=SubstrateDesign.NONE)
# Optionally set back side settings if printing both sides
cover.back_colours = Colours.PROCESS

spec.components.append(cover)

# 3) Validate only the COVER components using the specific component validator
cover_validator = CoverComponentValidator()
partial_result = ValidationResult()

for idx, comp in enumerate(spec.components):
    if comp.component_type == ComponentType.COVER:
        base_path = f"components[{idx}]"
        cover_validator.validate(pm, spec, comp, partial_result, base_path)

# 4) Inspect results from validating only the cover components
if partial_result.is_valid():
    print("All cover components are valid")
else:
    for err in partial_result.errors:
        print(f"{err.path}: {err.code} - {err.message}")
        if err.allowed:
            print(f"  allowed: {err.allowed}")
```

Notes and caveats:
- Prefer ProductItemSpecificationValidator for full validation because it also enforces top-level requirements (e.g., component counts, cross-component constraints) and runs primary-component rules.
- Component-only validation runs the base checks plus cover-specific rules implemented in CoverComponentValidator. It does not validate other component types present in the spec.
- The same pattern works for other component validators, e.g., DustJacketComponentValidator for dust jackets.
