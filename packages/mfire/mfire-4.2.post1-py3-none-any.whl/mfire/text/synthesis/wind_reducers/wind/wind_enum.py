from __future__ import annotations

from enum import Enum, IntEnum


class WindType(IntEnum):
    """Class to type the wind  regarding its force."""

    TYPE_1 = 1  # Low wind
    TYPE_2 = 2  # Middle wind
    TYPE_3 = 3  # High wind


class WindCase(Enum):
    """WindCase class."""

    CASE_1 = "1"
    CASE_2 = "2"
    CASE_3 = "3"
