from contextlib import nullcontext
from typing import Any
from unittest.mock import MagicMock

import pytest

from panda_pytest_assertions.assert_object import AsserterFactory, Stringified
from panda_pytest_assertions.assert_object._objects_asserters import StringifiedAsserter


@pytest.mark.parametrize(
    ['expectation', 'matches'],
    [
        (None, False),
        ('string', False),
        (Stringified('string'), True),
        (Stringified(''), True),
        (123, False),
        (123.123, False),
        (True, False),
        (False, False),
        ([], False),
        ({}, False),
        (object(), False),
    ],
)
def test_match(expectation: Any, matches: bool):
    assert StringifiedAsserter.matches(expectation) == matches


def test_init():
    expectation = MagicMock()
    asserter = StringifiedAsserter(AsserterFactory, expectation)

    assert asserter.expected_value == expectation.stringified_value
    assert asserter.asserter_factory is AsserterFactory


@pytest.mark.parametrize(
    ['expectation', 'object_', 'correct'],
    [
        (Stringified('None'), None, True),
        (Stringified('string'), None, False),
        (Stringified('string'), 'string', True),
        (Stringified('string'), 'string_', False),
        (Stringified('string'), '_string', False),
        (Stringified(r'{3: 4, 5: 7}'), {3: 4, 5: 7}, True),
        (Stringified('[3, 4, 5, 7]'), [3, 4, 5, 7], True),
        (Stringified("<class 'str'>"), str, True),
    ],
)
def test_assert_object(expectation: Any, object_: Any, correct: bool):
    with nullcontext() if correct else pytest.raises(AssertionError):
        StringifiedAsserter(AsserterFactory, expectation).assert_object(object_)
