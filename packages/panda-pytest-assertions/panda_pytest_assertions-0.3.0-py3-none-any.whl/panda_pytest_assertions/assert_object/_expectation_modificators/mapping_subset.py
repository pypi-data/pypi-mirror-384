from collections.abc import Mapping
from typing import Any


class MappingSubset:
    """
    Wrapper for the expectation that describes a subset of a mapping object.
    """

    def __init__(self, items_expectations: Mapping[Any, Any], /) -> None:
        #: mapping of items expectations
        self.items_expectations = items_expectations

    def __repr__(self) -> str:
        return f'MappingSubset({self.items_expectations!r})'
