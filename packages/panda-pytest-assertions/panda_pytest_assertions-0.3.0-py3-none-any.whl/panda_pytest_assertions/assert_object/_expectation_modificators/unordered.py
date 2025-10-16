from collections.abc import Iterator
from typing import Any


class Unordered:
    """
    Wrapper for the expectation that describes unordered list.
    """

    def __init__(self, elements_expectations: list[Any], /) -> None:
        #: list of elements expectations
        self.elements_expectations = elements_expectations

    def __iter__(self) -> Iterator[Any]:
        return iter(self.elements_expectations)

    def __repr__(self) -> str:
        return f'Unordered({self.elements_expectations!r})'
