from contextlib import nullcontext
from typing import Any
from unittest.mock import MagicMock

import pytest

from panda_pytest_assertions.assert_object import AsserterFactory, Is
from panda_pytest_assertions.assert_object._objects_asserters import IdentityAsserter


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
        (Is(''), True),
        (Is(None), True),
    ],
)
def test_match(expectation: Any, matches: bool):
    assert IdentityAsserter.matches(expectation) == matches


def test_init():
    value = MagicMock()

    expectation = Is(
        value,
    )
    asserter = IdentityAsserter(AsserterFactory, expectation)

    assert asserter.expected_object is value
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
        (Is(None), None, True),
        (Is('abc'), None, False),
        (Is(None), 'abc', False),
        (Is('abc'), 'abc', True),
        (Is({}), {}, False),
        (Is({}), '{}', False),
        (Is('{}'), {}, False),
        (Is(object()), object(), False),
        (Is(obj := object()), obj, True),
    ],
)
def test_assert_object(expectation: Any, object_: Any, correct: bool):
    with nullcontext() if correct else pytest.raises(AssertionError):
        IdentityAsserter(AsserterFactory, expectation).assert_object(object_)
