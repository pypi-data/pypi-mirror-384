import sys
from contextlib import nullcontext
from ipaddress import IPv4Address
from typing import Any
from unittest.mock import MagicMock

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object import AsserterFactory, WithType
from panda_pytest_assertions.assert_object._objects_asserters import WithTypeAsserter

from .conftest import DummyAsserter


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
        (WithType(None, '', None), True),
        (WithType('string', '', None), True),
        (WithType(123, '', 'module name'), True),
        (WithType(123.123, 'abc', 'some module'), True),
        (WithType(True, '', None), True),  # noqa: FBT003
        (WithType(False, 'xyz', None), True),  # noqa: FBT003
        (WithType([], '', None), True),
        (WithType({}, '', None), True),
        (WithType(object(), '', None), True),
    ],
)
def test_match(expectation: Any, matches: bool):
    assert WithTypeAsserter.matches(expectation) == matches


def test_init():
    expected_type_name = MagicMock()
    expected_type_module = MagicMock()

    expectation = WithType(
        'some string',
        expected_type_name,
        expected_type_module,
    )
    asserter = WithTypeAsserter(AsserterFactory, expectation)

    assert asserter.expected_type_name is expected_type_name
    assert asserter.expected_type_module is expected_type_module
    assert asserter.object_asserter == DummyAsserter(AsserterFactory, 'some string')
    assert asserter.asserter_factory is AsserterFactory


class EqualsNone:  # noqa: PLW1641
    def __eq__(self, value: object) -> bool:
        return value is None


class NotEqualsNone:  # noqa: PLW1641
    def __eq__(self, value: object) -> bool:
        return value is not None


if sys.version_info >= (3, 14):
    IPV4_10_MUNCH: Munch[Any, Any] = Munch(_ip=10, version=4)
    IPV4_11_MUNCH: Munch[Any, Any] = Munch(_ip=11, version=4)
else:
    IPV4_10_MUNCH: Munch[Any, Any] = Munch(_ip=10, _version=4)
    IPV4_11_MUNCH: Munch[Any, Any] = Munch(_ip=11, _version=4)


@pytest.mark.parametrize(
    ['expectation', 'object_', 'correct'],
    [
        (WithType(None, 'NoneType', 'builtins'), None, True),
        (WithType(None, 'xxx NoneType', 'builtins'), None, False),
        (WithType(None, 'NoneType xxx', 'builtins'), None, False),
        (WithType(None, 'NoneType', 'xxx builtins'), None, False),
        (WithType(None, 'NoneType', 'builtins xxx'), None, False),
        (WithType('abc', 'NoneType', 'builtins'), None, False),
        (WithType(None, 'NoneType', None), None, True),
        (WithType(None, 'xxx NoneType', None), None, False),
        (WithType(None, 'NoneType xxx', None), None, False),
        (WithType('abc', 'NoneType', None), None, False),
        (WithType(EqualsNone(), 'NoneType', 'builtins'), None, True),
        (WithType(NotEqualsNone(), 'NoneType', 'builtins'), None, False),
        (WithType(IPV4_10_MUNCH, 'IPv4Address', 'ipaddress'), IPv4Address('0.0.0.10'), True),
        (WithType(IPV4_10_MUNCH, 'IPv4Address', None), IPv4Address('0.0.0.10'), True),
        (WithType(IPV4_10_MUNCH, 'IPv4Address', 'NOT ipaddress'), IPv4Address('0.0.0.10'), False),
        (WithType(IPV4_10_MUNCH, 'IPv6Address', 'ipaddress'), IPv4Address('0.0.0.10'), False),
        (WithType(IPV4_10_MUNCH, 'IPv6Address', None), IPv4Address('0.0.0.10'), False),
        (WithType(IPV4_11_MUNCH, 'IPv4Address', 'ipaddress'), IPv4Address('0.0.0.10'), False),
    ],
)
def test_assert_object(expectation: Any, object_: Any, correct: bool):
    with nullcontext() if correct else pytest.raises(AssertionError):
        WithTypeAsserter(AsserterFactory, expectation).assert_object(object_)
