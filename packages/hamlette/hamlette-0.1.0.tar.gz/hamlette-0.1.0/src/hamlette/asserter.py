import os
from typing import Any, Callable

import hamcrest as hc
from hamcrest.core.matcher import Matcher
from hamcrest.core.string_description import StringDescription

type MatcherAndReason[T] = Matcher[T] | tuple[Matcher[T], str]
type ValueAndReason[T] = T | tuple[T, str]


class FluentAsserter:
    """
    A fluent assertion entry point that provides a chainable and expressive API for assertions.

    Instead of direct instantiation, use the `that` function to create an instance.
    """

    def __init__(self, actual: Any, **kwargs) -> None:
        self._actual: Any = actual
        self._single_line: bool = kwargs.get("single_line", False)

    def _assert(self, matcher: MatcherAndReason[Any]) -> bool:
        matcher, reason = matcher if isinstance(matcher, tuple) else (matcher, "")
        self._do_match(self._actual, matcher, reason)
        return True

    def _do_match(self, actual: Any, matcher: Matcher[Any], reason: str) -> None:
        if not matcher.matches(actual):
            raise AssertionError(self._prepare_message(actual, matcher, reason))

    def _prepare_message(self, actual: Any, matcher: Matcher[Any], reason: str) -> str:
        func = self._prepare_single_line_message if self._single_line else self._prepare_multiline_message
        return str(func(actual, matcher, reason))

    @staticmethod
    def _prepare_single_line_message(actual: Any, matcher: Matcher[Any], reason: str) -> str:
        desc: StringDescription = StringDescription()

        if reason:
            reason = reason.rstrip(" .")
            desc.append_text(reason).append_text(". ")

        # Append the expected description...
        desc.append_text("Expected ") \
            .append_description_of(matcher) \
            .append_text(", but ")

        # Append the mismatch description...
        matcher.describe_mismatch(actual, desc)

        return str(desc)

    @staticmethod
    def _prepare_multiline_message(actual: Any, matcher: Matcher[Any], reason: str) -> str:
        desc: StringDescription = StringDescription()

        # Append the expected description...
        desc.append_text(reason.strip()) \
            .append_text("\nExpected: ") \
            .append_description_of(matcher) \
            .append_text("\n     but: ")

        # Append the mismatch description...
        matcher.describe_mismatch(actual, desc)
        desc.append_text("\n")

        return str(desc)

    # Enables a usage like: `that(x) >> matcher` to assert x satisfies matcher.
    __rshift__ = _assert

    def _assert_value(self, value: ValueAndReason[Any], matcher: Callable[[Any], Matcher[Any]]) -> bool:
        value, reason = value if isinstance(value, tuple) else (value, "")
        return self._assert((matcher(value), reason))

    def __eq__(self, value: ValueAndReason[Any]) -> bool:
        """Enables a usage like: `that(x) == y` to assert x equals y."""
        return self._assert_value(value, hc.equal_to)

    def __ne__(self, value: ValueAndReason[Any]) -> bool:
        """Enables a usage like: `that(x) != y` to assert x not equals y."""
        return self._assert_value(value, hc.is_not)

    def __gt__(self, value: ValueAndReason[Any]) -> bool:
        """Enables a usage like: `that(x) > y` to assert x greater than y."""
        return self._assert_value(value, hc.greater_than)

    def __ge__(self, value: ValueAndReason[Any]) -> bool:
        """Enables a usage like: `that(x) >= y` to assert x greater than or equal to y."""
        return self._assert_value(value, hc.greater_than_or_equal_to)

    def __lt__(self, value: ValueAndReason[Any]) -> bool:
        """Enables a usage like: `that(x) < y` to assert x less than y."""
        return self._assert_value(value, hc.less_than)

    def __le__(self, value: ValueAndReason[Any]) -> bool:
        """Enables a usage like: `that(x) <= y` to assert x less than or equal to y."""
        return self._assert_value(value, hc.less_than_or_equal_to)


def that(actual: Any) -> FluentAsserter:
    """
    Asserts that the given actual value satisfies the matcher given in the chained call. This provides a
    fluent API for writing assertion statements.

    It enables a more readable and expressive way to write assertions, similar to natural language by overloading
    operators like `==`, `!=`, `>`, `<`, `>=`, and `<=` for comparison and using `>>` to apply custom matchers.

    Examples:
    ```python
    >>> from hamlette import greater_than, less_than
    >>>
    >>> x: int = 5
    >>>
    >>> # Comparison assertions
    >>> that(x) == 5
    >>> that(x) != 3
    >>> that(x) > 3
    >>> that(x) <= 7
    >>>
    >>> # Custom matchers (using `>>` operator)
    >>> that(x) >> greater_than(3)
    ```
    """
    return FluentAsserter(
        actual,
        single_line=os.environ.get("HAMLETTE_SINGLE_LINE", "0") == "1",
    )


__all__ = [
    "that",
]
