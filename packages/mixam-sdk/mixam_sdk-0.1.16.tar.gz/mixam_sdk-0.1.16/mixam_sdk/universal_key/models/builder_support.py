from __future__ import annotations

from dataclasses import is_dataclass, fields as dc_fields
from decimal import Decimal
from typing import Any, Dict, Mapping

from pydantic import BaseModel

from mixam_sdk.item_specification.interfaces.component_protocol import Member, Container


class BuilderSupport:
    def collect_member_tokens(self, component: Any) -> Dict[str, str]:
        return self._collect_member_tokens("", component)

    def _value_to_string(self, value: Any) -> str | None:
        if value is None:
            return None
        # Booleans
        if isinstance(value, bool):
            return "1" if value else None
        # Integers
        if isinstance(value, int) and not isinstance(value, bool):
            return str(value) if value != 0 else None
        # Decimal / float
        if isinstance(value, (Decimal, float)):
            try:
                d = Decimal(str(value))
            except Exception:
                return None
            return str(d.normalize()) if d != 0 else None
        # Enums or value-based
        for attr in ("value", "code", "name"):
            if hasattr(value, attr):
                v = getattr(value, attr)
                # Numeric case
                if isinstance(v, int):
                    return str(v) if v != 0 else None
                # String case -> treat NONE/"" as default
                if isinstance(v, str):
                    if v and v != "NONE":
                        return v
                    return None
        return None

    def _collect_member_tokens(self, context: str, structure: Any) -> Dict[str, str]:
        tokens: Dict[str, str] = {}

        if isinstance(structure, BaseModel):
            model: BaseModel = structure
            for name, field in type(model).model_fields.items():
                info = field.json_schema_extra or {}
                container = info.get("container") if isinstance(info, Mapping) else None
                member = info.get("member") if isinstance(info, Mapping) else None
                value = getattr(model, name)
                if container and isinstance(container, Container):
                    if value is not None:
                        sub = self._collect_member_tokens(container.code, value)
                        tokens.update(sub)
                elif member and isinstance(member, Member):
                    s = self._value_to_string(value)
                    if s is not None:
                        self._add_token(tokens, f"{context}{member.code}", s)
            return dict(sorted(tokens.items()))

        # Dataclass
        if is_dataclass(structure):
            for f in dc_fields(structure):
                info = f.metadata or {}
                value = getattr(structure, f.name)
                container = info.get("container")
                member = info.get("member")
                if isinstance(container, Container):
                    if value is not None:
                        sub = self._collect_member_tokens(container.code, value)
                        tokens.update(sub)
                elif isinstance(member, Member):
                    s = self._value_to_string(value)
                    if s is not None:
                        self._add_token(tokens, f"{context}{member.code}", s)
            return dict(sorted(tokens.items()))
        return dict(sorted(tokens.items()))

    def _add_token(self, tokens: Dict[str, str], key: str, value: str) -> None:
        if key in tokens:
            existing = tokens[key]
            raise ValueError(
                f"Cannot add value '{value}' for token '{key}' because the value '{existing}' is already present"
            )
        tokens[key] = value
