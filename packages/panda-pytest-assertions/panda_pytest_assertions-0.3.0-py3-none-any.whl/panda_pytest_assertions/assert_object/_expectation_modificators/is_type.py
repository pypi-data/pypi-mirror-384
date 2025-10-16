from typing import Any, overload


class IsType:
    """
    Wrapper for the expectation that checks object's type.
    """

    def __init__(
        self,
        expected_type_name: str,
        expected_type_module: str | None,
        /,
    ) -> None:
        #: expected name of the object type
        self.expected_type_name = expected_type_name
        #: expected module of the object type
        self.expected_type_module = expected_type_module

    def __repr__(self) -> str:
        return (
            f'IsType('
            f'expected_type_name={self.expected_type_name!r}, '
            f'expected_type_module={self.expected_type_module!r}'
            f')'
        )


@overload
def is_type(value_type: type[Any], /) -> IsType:  # noqa: D418
    """
    Create IsType expectation asserting object type.

    Expected type name and type module will be extracted from the provided type.

    :param value_type: type to extract expected type name and module from
    """


@overload
def is_type(  # noqa: D418
    value_type_name: str,
    value_type_module: str | None = None,
    /,
) -> IsType:
    """
    Create IsType expectation asserting object type.

    Expected type name will be equal to `value_type_name` and expected module name will be
    equal to `value_type_module` (which can be not set if is not supposed to be asserted).

    :param value_type_name: name of the expected type
    :param value_type_module: module of the expected type
    """


def is_type(
    value_type: type[Any] | str,
    value_type_module: str | None = None,
    /,
) -> IsType:
    """
    Create IsType expectation asserting object type.

    If `value_type` is a type, expected type name and type module will be extracted from this type.

    If `value_type` is a string, expected type name will be equal to it and expected module name will be
    equal to provided `value_type_module` (which can be not set if is not supposed to be asserted).

    :param value_type: expected type or name of the type
    :param value_type_module: expected type's module
    :return: created expectation
    """
    match value_type, value_type_module:
        case str(), str() | None:
            expected_type_name = value_type
            expected_type_module = value_type_module
        case type(), None:
            expected_type_name = value_type.__name__
            expected_type_module = value_type.__module__
        case _:
            msg = (
                f'IsType helper constructor does not accept the following arguments: '
                f'{(value_type, value_type_module)}'
            )
            raise ValueError(msg)
    return IsType(
        expected_type_name,
        expected_type_module,
    )
