from decimal import Decimal
from typing import Protocol, Self

type Number = float | int | Decimal
"""A type alias for numeric types including float, int, and Decimal."""


class Comparable(Protocol):
    """A protocol for comparable types that support less-than comparison."""

    def __lt__(self, other: Self) -> bool: ...


__all__ = [
    'Number',
    'Comparable',
]
