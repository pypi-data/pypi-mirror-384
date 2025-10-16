from typing import Any


class UniformMappingDef:
    """
    Defines mapping expectation where all keys and values share common definitions.
    """

    def __init__(self, keys_definition: Any, values_definition: Any, /) -> None:  # noqa: ANN401
        #: definition for mapping keys
        self.keys_definition = keys_definition
        #: definition for mapping values
        self.values_definition = values_definition
