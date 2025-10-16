from contextlib import nullcontext
from ipaddress import IPv4Address
from typing import Any
from unittest.mock import MagicMock

import pytest

from panda_pytest_assertions.assert_object import AsserterFactory, IsType
from panda_pytest_assertions.assert_object._objects_asserters import IsTypeAsserter


@pytest.mark.parametrize(
    ['expectation', 'matches'],
    [
        (None, False),
        ('string', False),
        (123, False),
        (123.123, False),
        (True, False),
        (False, False),
        ([], False),
        ({}, False),
        (object(), False),
        (IsType('', None), True),
        (IsType('xyz', None), True),
        (IsType('', 'module name'), True),
        (IsType('abc', 'some module'), True),
    ],
)
def test_match(expectation: Any, matches: bool):
    assert IsTypeAsserter.matches(expectation) == matches


def test_init():
    expected_type_name = MagicMock()
    expected_type_module = MagicMock()

    expectation = IsType(
        expected_type_name,
        expected_type_module,
    )
    asserter = IsTypeAsserter(AsserterFactory, expectation)

    assert asserter.expected_type_name is expected_type_name
    assert asserter.expected_type_module is expected_type_module
    assert asserter.asserter_factory is AsserterFactory


class EqualsNone:  # noqa: PLW1641
    def __eq__(self, value: object) -> bool:
        return value is None


class NotEqualsNone:  # noqa: PLW1641
    def __eq__(self, value: object) -> bool:
        return value is not None


@pytest.mark.parametrize(
    ['expectation', 'object_', 'correct'],
    [
        (IsType('NoneType', 'builtins'), None, True),
        (IsType('xxx NoneType', 'builtins'), None, False),
        (IsType('NoneType xxx', 'builtins'), None, False),
        (IsType('NoneType', 'xxx builtins'), None, False),
        (IsType('NoneType', 'builtins xxx'), None, False),
        (IsType('NoneType', None), None, True),
        (IsType('xxx NoneType', None), None, False),
        (IsType('NoneType xxx', None), None, False),
        (IsType('IPv4Address', 'ipaddress'), IPv4Address('0.0.0.10'), True),
        (IsType('IPv4Address', None), IPv4Address('0.0.0.10'), True),
        (IsType('IPv4Address', 'NOT ipaddress'), IPv4Address('0.0.0.10'), False),
        (IsType('IPv6Address', 'ipaddress'), IPv4Address('0.0.0.10'), False),
        (IsType('IPv6Address', None), IPv4Address('0.0.0.10'), False),
    ],
)
def test_assert_object(expectation: Any, object_: Any, correct: bool):
    with nullcontext() if correct else pytest.raises(AssertionError):
        IsTypeAsserter(AsserterFactory, expectation).assert_object(object_)
