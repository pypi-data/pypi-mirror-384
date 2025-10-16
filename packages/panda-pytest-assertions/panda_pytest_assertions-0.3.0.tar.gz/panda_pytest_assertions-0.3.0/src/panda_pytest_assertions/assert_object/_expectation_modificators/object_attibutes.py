from collections.abc import Mapping
from typing import Any


class ObjectAttributes:
    """
    Wrapper for the expectation that describes a object attributes.
    """

    def __init__(self, attributes_expectations: Mapping[str, Any], /) -> None:
        #: mapping of attributes expectations
        self.attributes_expectations = attributes_expectations

    def __repr__(self) -> str:
        return f'ObjectAttributes({self.attributes_expectations!r})'
