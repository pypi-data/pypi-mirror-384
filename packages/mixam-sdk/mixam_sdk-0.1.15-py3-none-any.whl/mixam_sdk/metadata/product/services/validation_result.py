from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class ValidationMessage:
    path: str
    message: str
    code: str
    allowed: list[Any] | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, item: str) -> Any:
        if item in self.__dict__:
            return self.__dict__[item]
        if item in self.extra:
            return self.extra[item]
        raise AttributeError(item)

    def as_kv_list(self) -> list[tuple[str, Any]]:
        base = [("path", self.path), ("message", self.message), ("code", self.code)]
        if self.allowed is not None:
            base.append(("allowed", self.allowed))
        for k, v in self.extra.items():
            if k not in {"path", "message", "code", "allowed"}:
                base.append((k, v))
        return base

    def humanize(self) -> str:
        pairs = [f"{k}={v}" for k, v in self.as_kv_list()]
        return ", ".join(pairs)


class ValidationResult:
    def __init__(self) -> None:
        self.errors: List[ValidationMessage] = []
        self.warnings: List[ValidationMessage] = []

    def add_error(self, path: str, message: str, code: str, **kwargs: Any) -> None:
        allowed = kwargs.pop("allowed", None)
        msg = ValidationMessage(path=path, message=message, code=code, allowed=allowed, extra=kwargs)
        self.errors.append(msg)

    def is_valid(self) -> bool:
        return len(self.errors) == 0


__all__ = ["ValidationMessage", "ValidationResult"]
