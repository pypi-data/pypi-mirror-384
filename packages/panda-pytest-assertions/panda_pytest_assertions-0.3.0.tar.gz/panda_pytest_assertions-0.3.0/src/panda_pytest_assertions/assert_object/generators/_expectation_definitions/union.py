from typing import Any


class UnionDef:
    """
    Definition that accepts multiple definitions in case a place in object can have multiple types of values.

    The first definition that matches a value during expectation generation will be used.
    """

    def __init__(self, *definitions: Any) -> None:  # noqa: ANN401
        #: allowed union definitions
        self.definitions = definitions
