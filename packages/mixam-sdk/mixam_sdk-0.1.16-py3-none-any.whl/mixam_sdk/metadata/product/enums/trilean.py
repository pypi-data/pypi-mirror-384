from __future__ import annotations

from enum import Enum


class Trilean(Enum):
    UNAVAILABLE = "UNAVAILABLE"
    OPTIONAL = "LBS_TEXT"
    REQUIRED = "REQUIRED"
