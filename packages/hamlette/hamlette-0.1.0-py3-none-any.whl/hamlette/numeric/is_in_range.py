from __future__ import annotations

from typing import Any

from hamcrest.core.base_matcher import BaseMatcher
from hamcrest.core.description import Description

from ..utils.types import Comparable


class IsInRange[T: Comparable](BaseMatcher[T]):
    """Matcher that checks if a value is within a specified range."""

    def __init__(self, start: T, end: T, includes_start: bool = True, includes_end: bool = False):
        self._start: T = start
        self._end: T = end
        self._includes_start: bool = includes_start
        self._includes_end: bool = includes_end

    def start_excluded(self) -> IsInRange:
        """Returns a new matcher instance with the start value excluded from the range."""
        return IsInRange(self._start, self._end, includes_start=False, includes_end=self._includes_end)

    def end_included(self) -> IsInRange:
        """Returns a new matcher instance with the end value included in the range."""
        return IsInRange(self._start, self._end, includes_start=self._includes_start, includes_end=True)

    def _matches(self, item: T) -> bool:
        if self._includes_start:  # [...
            if item < self._start:  # item < start
                return False
        elif not item > self._start:  # item <= self._start
            return False

        if self._includes_end:  # ...]
            if item > self._end:  # item > end
                return False
        elif not item < self._end:  # item >= self._end
            return False

        return True

    def describe_to(self, description: Description) -> None:
        description.append_text("a value in range ")
        description.append_text("[" if self._includes_start else "(")
        description.append_description_of(self._start)
        description.append_text(", ")
        description.append_description_of(self._end)
        description.append_text("]" if self._includes_end else ")")


def in_range(start: Any, end: Any, includes_start: bool = True, includes_end: bool = False) -> IsInRange[Any]:
    """
    Matches if evaluated object is within a given range.

    By default, the range is start-inclusive and end-exclusive. This can be changed by setting the `includes_start`
    and `includes_end` parameters. Or, you can use the `start_excluded()` and `end_included()` methods on the returned
    matcher to create a new matcher with the desired inclusivity.

    Examples:
        assert that(x) >> in_range(1, 10)  # 1 <= x < 10
        assert that(x) >> in_range(1, 10).start_excluded()  # 1 < x < 10
        assert that(x) >> in_range(1, 10).end_included()  # 1 <= x <= 10
        assert that(x) >> in_range(1, 10, includes_start=False, includes_end=True)  # 1 < x <= 10

    Args:
        start: lower bound of the range
        end: upper bound of the range
        includes_start: whether the start value is included in the range (default: True)
        includes_end: whether the end value is included in the range (default: False)

    Returns:
        An IsInRange matcher instance.
    """
    return IsInRange(start, end, includes_start, includes_end)


is_in_range = in_range
"""An alias for `in_range` matcher for improved readability."""

__all__ = [
    "in_range",
    "is_in_range",
]
