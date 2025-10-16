from __future__ import annotations

from dataclasses import is_dataclass, fields as dc_fields, MISSING
from decimal import Decimal
from typing import Any, Dict, Mapping, Type

from pydantic import BaseModel

from mixam_sdk.item_specification.interfaces.component_protocol import Member, Container


class ParserSupport:
    """
    Mirror of BuilderSupport but in reverse: given a mapping of member tokens
    (e.g. {"5c": "", "4f": ""} separated into code/value), populate a
    component model instance.
    """

    def assemble_member_tokens(self, member_tokens: Dict[str, str], cls: Type[Any]) -> Any:
        # Copy so we can track leftovers
        tokens = dict(member_tokens)
        instance, _ = self._build_from_tokens("", tokens, cls)
        if tokens:
            # Some tokens unused -> raise to mimic Java behavior
            raise RuntimeError(f"Member tokens collection contained unused data: {tokens}")
        return instance

    def _create_instance(self, cls: Type[Any]) -> Any:
        # For pydantic BaseModel, we can instantiate with no args; defaults will be applied
        if issubclass(cls, BaseModel):
            return cls()  # type: ignore[call-arg]
        # Fallback: dataclass or simple class with no-arg ctor
        try:
            return cls()
        except Exception as e:
            raise RuntimeError(f"Unable to instantiate {cls}: {e}")

    def _resolve_annotation_type(self, ann: Any) -> type:
        # Handle Annotated, Optional/Union, etc.
        origin = getattr(ann, "__origin__", None)
        if origin is not None:
            if str(origin).endswith("Annotated") and hasattr(ann, "__args__"):
                return self._resolve_annotation_type(ann.__args__[0])
            if origin is getattr(__import__('typing'), 'Union', None) or str(origin).endswith('Union'):
                args = [a for a in getattr(ann, "__args__", ()) if a is not type(None)]  # noqa: E721
                if args:
                    return self._resolve_annotation_type(args[0])
                return object
        # Python 3.10+ X | Y unions
        import types
        if isinstance(ann, types.UnionType):
            args = [a for a in ann.__args__ if a is not type(None)]  # type: ignore[attr-defined]
            if args:
                return self._resolve_annotation_type(args[0])
            return object
        # Default
        return ann if isinstance(ann, type) else type(ann)

    def _build_from_tokens(self, context: str, tokens: Dict[str, str], cls_or_instance: Type[Any] | Any) -> tuple[Any, bool]:
        # Accept either a class or an existing instance to guide type info
        cls = cls_or_instance if isinstance(cls_or_instance, type) else type(cls_or_instance)

        # Pydantic BaseModel path: construct data dict then build instance
        if issubclass(cls, BaseModel):
            used_any = False
            data: Dict[str, Any] = {}
            model_fields = cls.model_fields  # type: ignore[attr-defined]
            for name, field in model_fields.items():
                info = field.json_schema_extra or {}
                info = info if isinstance(info, Mapping) else {}
                container = info.get("container")
                member = info.get("member")
                if isinstance(container, Container):
                    ann = field.annotation  # type: ignore[attr-defined]
                    sub_cls = self._resolve_annotation_type(ann)
                    sub_obj, sub_used = self._build_from_tokens(container.code, tokens, sub_cls)
                    if sub_used:
                        data[name] = sub_obj
                        used_any = True
                elif isinstance(member, Member):
                    code = f"{context}{member.code}"
                    v = tokens.pop(code, None)
                    if v is not None:
                        target_type = field.annotation  # type: ignore[attr-defined]
                        parsed = self._parse_value_for_field(getattr(target_type, "__origin__", target_type), v)
                        data[name] = parsed
                        used_any = True
            instance = cls(**data)
            return instance, used_any

        # Dataclass path: similar handling
        if is_dataclass(cls):
            used_any = False
            kwargs: Dict[str, Any] = {}
            for f in dc_fields(cls):
                info = f.metadata or {}
                container = info.get("container")
                member = info.get("member")
                if isinstance(container, Container):
                    sub_obj, sub_used = self._build_from_tokens(container.code, tokens, f.type)
                    if sub_used:
                        kwargs[f.name] = sub_obj
                        used_any = True
                elif isinstance(member, Member):
                    code = f"{context}{member.code}"
                    v = tokens.pop(code, None)
                    if v is not None:
                        parsed = self._parse_value_for_field(f.type, v)
                        kwargs[f.name] = parsed
                        used_any = True
            try:
                return cls(**kwargs), used_any
            except Exception:
                return self._create_instance(cls), used_any

        # Fallback: create instance with no args
        return self._create_instance(cls), False

    def _parse_value_for_field(self, field_type: Type[Any], value: str) -> Any:
        # Booleans: any presence is True
        if field_type is bool:
            return True
        # Integers
        if field_type is int:
            return int(value)
        # Decimal
        if field_type is Decimal:
            return Decimal(value)
        # Enums or ValueBased-like with .__members__ or pydantic Enum
        # We try common attributes in our project: name, value, code
        # If target is a subclass of Enum, attempt by value (int) or name (str)
        try:
            import enum
            if issubclass(field_type, enum.Enum):
                # prefer numeric value
                try:
                    iv = int(value)
                    for m in field_type:  # type: ignore[assignment]
                        v = getattr(m, "value", None)
                        if v == iv:
                            return m
                except Exception:
                    pass
                # fallback by name
                return field_type[value]
        except Exception:
            pass
        # If field_type has a classmethod for value-based lookup
        for meth in ("for_value", "from_value"):
            func = getattr(field_type, meth, None)
            if callable(func):
                return func(int(value))
        # Last resort: return original string
        return value
