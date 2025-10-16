from collections.abc import Callable
from typing import Any, overload


class WithType:
    """
    Wrapper for the expectation that additionally checks object's type.
    """

    def __init__(
        self,
        expectation: Any,  # noqa: ANN401
        expected_type_name: str,
        expected_type_module: str | None,
        /,
    ) -> None:
        #: object expectation
        self.expectation = expectation
        #: expected name of the object type
        self.expected_type_name = expected_type_name
        #: expected module of the object type
        self.expected_type_module = expected_type_module

    def __repr__(self) -> str:
        return (
            f'WithType('
            f'expectation={self.expectation!r}, '
            f'expected_type_name={self.expected_type_name!r}, '
            f'expected_type_module={self.expected_type_module!r}'
            f')'
        )


#: type alias to simplify definitions below
_WithTypeCreator = Callable[[Any], WithType]


@overload
def with_type() -> _WithTypeCreator:  # noqa: D418
    """
    Return the function that will accept an object and create expectations additionally asserting object type.

    Returned function accepts any kind of value and will create proper expectation.

    Expected type name and type module will be extracted from the object passed to the returned function.
    """


@overload
def with_type(value_type: type[Any], /) -> _WithTypeCreator:  # noqa: D418
    """
    Return the function that will accept an object and create expectations additionally asserting object type.

    Returned function accepts any kind of value and will create proper expectation.

    Expected type name and type module will be extracted from the provided type type.

    :param value_type: type to extract expected type name and module from
    """


@overload
def with_type(  # noqa: D418
    value_type_name: str,
    value_type_module: str | None = None,
    /,
) -> _WithTypeCreator:
    """
    Return the function that will accept an object and create expectations additionally asserting object type.

    Returned function accepts any kind of value and will create proper expectation.

    Expected type name will be equal to `value_type_name` and expected module name will be
    equal to `value_type_module` (which can be not set if is not supposed to be asserted).

    :param value_type_name: name of the expected type
    :param value_type_module: module of the expected type
    """


def with_type(
    value_type: type[Any] | str | None = None,
    value_type_module: str | None = None,
    /,
) -> _WithTypeCreator:
    """
    Return the function that will accept an object and create expectations additionally asserting object type.

    Returned function accepts any kind of value and will create WithType expectation.

    If `value_type` parameter is not set, expected type name and type module will be extracted from the object
    passed to the returned function.

    If `value_type` is a type, expected type name and type module will be extracted from this type.

    If `value_type` is a string, expected type name will be equal to it and expected module name will be
    equal to provided `value_type_module` (which can be not set if is not supposed to be asserted).

    :param value_type: expected type or name of the type
    :param value_type_module: expected type's module
    :return: function that will take create proper type-aware expectation
    """
    match value_type, value_type_module:
        case None, None:
            expected_type_name = None
            expected_type_module = None
        case type(), None:
            assert isinstance(value_type, type)
            expected_type_name = value_type.__name__
            expected_type_module = value_type.__module__
        case str(), str() | None:
            assert isinstance(value_type, str)
            expected_type_name = value_type
            expected_type_module = value_type_module
        case _:
            msg = (
                f'WithType helper constructor does not accept the following arguments: '
                f'{(value_type, value_type_module)}'
            )
            raise ValueError(msg)

    def _creator(expectation: Any) -> WithType:  # noqa: ANN401
        if expected_type_name is None:
            return WithType(
                expectation,
                expectation.__class__.__name__,
                expectation.__class__.__module__,
            )
        return WithType(
            expectation,
            expected_type_name,
            expected_type_module,
        )

    return _creator
