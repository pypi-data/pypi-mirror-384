from ipaddress import IPv4Address
from typing import Any
from unittest.mock import MagicMock

import pytest

from panda_pytest_assertions.assert_object import with_type, WithType


def test_init():
    expectation = MagicMock()
    type_name = 'some type name'
    type_module = 'some type module'

    instance = WithType(expectation, type_name, type_module)

    assert instance.expectation is expectation
    assert instance.expected_type_name == type_name
    assert instance.expected_type_module == type_module


def test_repr():
    expectation = MagicMock()
    type_name = 'some type name'
    type_module = 'some type module'

    instance = WithType(expectation, type_name, type_module)

    assert repr(instance) == (
        f'WithType('
        f'expectation={expectation!r}, '
        f'expected_type_name={type_name!r}, '
        f'expected_type_module={type_module!r}'
        f')'
    )


def equal(left: WithType, right: WithType) -> bool:
    return (
        isinstance(left, WithType)
        and isinstance(right, WithType)
        and left.expectation == right.expectation
        and left.expected_type_name == right.expected_type_name
        and left.expected_type_module == right.expected_type_module
    )


@pytest.mark.parametrize(
    ['value_type', 'value_type_module', 'value', 'expected'],
    [
        # no arguments
        (None, None, None, WithType(None, 'NoneType', 'builtins')),
        (None, None, 'something', WithType('something', 'str', 'builtins')),
        (
            None,
            None,
            IPv4Address('192.168.1.1'),
            WithType(IPv4Address('192.168.1.1'), 'IPv4Address', 'ipaddress'),
        ),
        # value type as type
        (str, None, None, WithType(None, 'str', 'builtins')),
        (int, None, 'something', WithType('something', 'int', 'builtins')),
        (
            MagicMock,
            None,
            IPv4Address('192.168.1.1'),
            WithType(IPv4Address('192.168.1.1'), 'MagicMock', 'unittest.mock'),
        ),
        # value type as string, no module
        ('str', None, None, WithType(None, 'str', None)),
        ('int', None, 'something', WithType('something', 'int', None)),
        (
            'MagicMock',
            None,
            IPv4Address('192.168.1.1'),
            WithType(IPv4Address('192.168.1.1'), 'MagicMock', None),
        ),
        # value type as string with module
        ('str', 'some module', None, WithType(None, 'str', 'some module')),
        ('int', 'some module', 'something', WithType('something', 'int', 'some module')),
        (
            'MagicMock',
            'some module',
            IPv4Address('192.168.1.1'),
            WithType(IPv4Address('192.168.1.1'), 'MagicMock', 'some module'),
        ),
    ],
)
def test_with_type_function(
    value_type: type[Any] | str | None,
    value_type_module: str | None,
    value: Any,
    expected: WithType,
):
    assert equal(
        with_type(value_type, value_type_module)(value),  # type: ignore [arg-type]
        expected,
    )


@pytest.mark.parametrize(
    ['value_type', 'value_type_module'],
    [
        # invalid value_type type
        (123, None),
        # value_type is None
        (None, 'builtins'),
        (None, 123),
        (None, str),
        # value_type is a type
        (str, 'builtins'),
        (str, 123),
        (str, str),
        # value_type is a string
        ('some type', 123),
        ('some type', str),
    ],
)
def test_with_type_function_invalid_params(value_type: Any, value_type_module: Any):
    with pytest.raises(ValueError, match='WithType helper constructor'):
        with_type(value_type, value_type_module)
