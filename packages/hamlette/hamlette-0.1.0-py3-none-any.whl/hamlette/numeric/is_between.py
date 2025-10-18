from typing import Any

from hamcrest.core.description import Description

from .is_in_range import IsInRange
from ..utils.types import Comparable


class IsBetween[T: Comparable](IsInRange[T]):
    """Matcher that checks if a value is strictly between two values (both ends inclusive)."""

    def __init__(self, start: T, end: T):
        super().__init__(start, end, includes_start=True, includes_end=True)

    def describe_to(self, description: Description) -> None:
        description.append_text("a value between ")
        description.append_description_of(self._start)
        description.append_text(" and ")
        description.append_description_of(self._end)


def between(start: Any, end: Any) -> IsBetween[Any]:
    """
    Matches if evaluated object is strictly between two given values (both ends inclusive).

    Examples:
        assert that(x) >> between(1, 10)  # 1 <= x <= 10
    """
    return IsBetween(start, end)


is_between = between
"""Alias for `between` matcher."""

__all__ = [
    "between",
    "is_between",
]
