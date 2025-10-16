from contextlib import nullcontext
from typing import Any
from unittest.mock import MagicMock

import pytest

from panda_pytest_assertions.assert_object import AsserterFactory
from panda_pytest_assertions.assert_object._objects_asserters import EqualityAsserter


@pytest.mark.parametrize(
    ['expectation', 'matches'],
    [
        (None, True),
        ('string', True),
        (123, True),
        (123.123, True),
        (True, True),
        (False, True),
        ([], True),
        ({}, True),
        (object(), True),
    ],
)
def test_match(expectation: Any, matches: bool):
    assert EqualityAsserter.matches(expectation) == matches


def test_init():
    expectation = MagicMock()
    asserter = EqualityAsserter(AsserterFactory, expectation)

    assert asserter.expectation == expectation
    assert asserter.asserter_factory is AsserterFactory


@pytest.mark.parametrize(
    ['expectation', 'object_', 'correct'],
    [
        (None, None, True),
        (None, 0, False),
        (None, False, False),
        ('string', None, False),
        ('string', 'other string', False),
        ('string', 'string', True),
    ],
)
def test_assert_object(expectation: Any, object_: Any, correct: bool):
    with nullcontext() if correct else pytest.raises(AssertionError):
        EqualityAsserter(AsserterFactory, expectation).assert_object(object_)
