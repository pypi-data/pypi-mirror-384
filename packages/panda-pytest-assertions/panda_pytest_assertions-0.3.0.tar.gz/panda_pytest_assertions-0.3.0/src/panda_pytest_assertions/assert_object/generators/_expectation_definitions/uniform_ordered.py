from collections.abc import Callable
from typing import Any


class UniformOrderedDef:
    """
    Defines expectation for ordered collection using the same definition for each element.
    """

    def __init__(
        self,
        elements_definition: Any,  # noqa: ANN401
        /,
        *,
        expectation_type: type[list[Any]] | type[tuple[Any, ...]] = list,
    ) -> None:
        #: definition for elements
        self.elements_definition = elements_definition
        #: type of expectation to be generated
        self.expectation_type = expectation_type


def uniform_ordered_def(
    *,
    expectation_type: type[list[Any]] | type[tuple[Any, ...]] = list,
) -> Callable[[Any], UniformOrderedDef]:
    """
    Return the function that will accept elements definition and create expectation for ordered collection.

    Returned function accepts any kind of value that will be treated as elements definition for collection.

    :param expectation_type: defines which expectation type will be used
    :return: function creating definition
    """

    def _creator(elements_definition: Any, /) -> UniformOrderedDef:  # noqa: ANN401
        return UniformOrderedDef(elements_definition, expectation_type=expectation_type)

    return _creator
