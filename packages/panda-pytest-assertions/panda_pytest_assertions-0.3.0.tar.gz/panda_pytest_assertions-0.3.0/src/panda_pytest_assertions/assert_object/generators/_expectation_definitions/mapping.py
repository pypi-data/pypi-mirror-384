from collections.abc import Mapping
from typing import Any


class MappingDef:
    """
    Defines mapping expectation where all keys share common definition and each have definition for its value.
    """

    def __init__(self, keys_definition: Any, items_definitions: Mapping[str, Any], /) -> None:  # noqa: ANN401
        #: definition for mapping keys
        self.keys_definition = keys_definition
        #: mapping of items definitions
        self.items_definitions = items_definitions
