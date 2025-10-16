from typing import Any


class UniformUnorderedDef:
    """
    Defines expectation for unordered collection.
    """

    def __init__(self, elements_definition: Any, /) -> None:  # noqa: ANN401
        #: definition for elements
        self.elements_definition = elements_definition
