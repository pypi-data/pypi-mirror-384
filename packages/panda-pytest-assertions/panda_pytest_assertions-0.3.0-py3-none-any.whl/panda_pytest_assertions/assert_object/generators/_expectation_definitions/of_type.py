from typing import Any


class OfTypeDef:
    """
    Defines expectation that will only be generated if object is of a specific type.
    """

    def __init__(self, expected_type: type[Any] | None, object_definition: Any, /) -> None:  # noqa: ANN401
        #: type that the object needs to match for the expectation to be generated
        self.expected_type = expected_type
        #: definition for object itself
        self.object_definition = object_definition
