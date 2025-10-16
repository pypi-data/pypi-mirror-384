from collections.abc import Mapping
from typing import Any


class ObjectAttributesDef:
    """
    Defines expectation for object attributes.
    """

    def __init__(self, attributes_definitions: Mapping[str, Any], /) -> None:
        #: mapping of attributes definitions
        self.attributes_definitions = attributes_definitions
