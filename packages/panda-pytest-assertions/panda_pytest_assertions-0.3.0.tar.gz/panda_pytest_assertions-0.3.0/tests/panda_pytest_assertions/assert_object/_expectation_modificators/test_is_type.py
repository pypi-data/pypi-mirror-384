from typing import Any
from unittest.mock import MagicMock

import pytest

from panda_pytest_assertions.assert_object import is_type, IsType


def test_init():
    type_name = 'some type name'
    type_module = 'some type module'

    instance = IsType(type_name, type_module)

    assert instance.expected_type_name == type_name
    assert instance.expected_type_module == type_module


def test_repr():
    type_name = 'some type name'
    type_module = 'some type module'

    instance = IsType(type_name, type_module)

    assert repr(instance) == (
        f'IsType(expected_type_name={type_name!r}, expected_type_module={type_module!r})'
    )


def equal(left: IsType, right: IsType) -> bool:
    return (
        isinstance(left, IsType)
        and isinstance(right, IsType)
        and left.expected_type_name == right.expected_type_name
        and left.expected_type_module == right.expected_type_module
    )


@pytest.mark.parametrize(
    ['value_type', 'value_type_module', 'expected'],
    [
        # value type as type
        (str, None, IsType('str', 'builtins')),
        (MagicMock, None, IsType('MagicMock', 'unittest.mock')),
        # value type as string, no module
        ('str', None, IsType('str', None)),
        ('MagicMock', None, IsType('MagicMock', None)),
        # value type as string with module
        ('str', 'some module', IsType('str', 'some module')),
        ('MagicMock', 'some module', IsType('MagicMock', 'some module')),
    ],
)
def test_is_type_function(
    value_type: type[Any] | str,
    value_type_module: str | None,
    expected: IsType,
):
    assert equal(
        is_type(value_type, value_type_module),  # type: ignore [arg-type]
        expected,
    )


@pytest.mark.parametrize(
    ['value_type', 'value_type_module'],
    [
        # invalid value_type type
        (123, None),
        # value_type is None
        (None, None),
        (None, 'builtins'),
        (None, 123),
        (None, str),
        # value_type is a type with value_type_module provided
        (str, 'builtins'),
        (str, 123),
        (str, str),
        # value_type is a string and value_type_module is not
        ('some type', 123),
        ('some type', str),
    ],
)
def test_is_type_function_invalid_params(value_type: Any, value_type_module: Any):
    with pytest.raises(ValueError, match='IsType helper constructor'):
        is_type(value_type, value_type_module)
