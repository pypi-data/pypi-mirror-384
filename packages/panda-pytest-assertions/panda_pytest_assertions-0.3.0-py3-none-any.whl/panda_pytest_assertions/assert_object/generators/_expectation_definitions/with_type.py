from collections.abc import Callable
from typing import Any


class WithTypeDef:
    """
    Defines expectation validating object type.
    """

    def __init__(self, object_definition: Any, /, *, include_module: bool = True) -> None:  # noqa: ANN401
        #: definition for object itself
        self.object_definition = object_definition
        #: indicator whether module shall be included in WithType expectation
        self.include_module = include_module


def with_type_def(*, include_module: bool = True) -> Callable[[Any], WithTypeDef]:
    """
    Return the function that will accept an object definition and create expectation definition with type.

    Returned function accepts any kind of value that will be treated as expectation definition for object.

    :param include_module: whether the module of the type shall be included in the expectation
    :return: function creating definition
    """

    def _creator(object_definition: Any, /) -> WithTypeDef:  # noqa: ANN401
        return WithTypeDef(object_definition, include_module=include_module)

    return _creator
