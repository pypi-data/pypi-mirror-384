from collections import Counter
from contextlib import nullcontext
from typing import Any

import pytest

from panda_pytest_assertions.assert_object import AsserterFactory, Unordered
from panda_pytest_assertions.assert_object._objects_asserters import UnorderedElementsAsserter

from .conftest import DummyAsserter


@pytest.mark.parametrize(
    ['expectation', 'matches'],
    [
        (None, False),
        ('string', False),
        (123, False),
        (True, False),
        (Unordered([]), True),
        (Unordered([123, 'abc']), True),
        (set(), True),
        ({123, 'abc'}, True),
        ({}, False),
        ({'123': '123'}, False),
        ({123: '123'}, False),
        (object(), False),
    ],
)
def test_match(expectation: Any, matches: bool):
    assert UnorderedElementsAsserter.matches(expectation) == matches


@pytest.mark.parametrize('expectation_type', [Unordered, set])
def test_init(expectation_type: type[set[Any]] | type[Unordered]):
    expectation = expectation_type(
        [
            'some string',
            123,
        ],
    )
    asserter = UnorderedElementsAsserter(AsserterFactory, expectation)

    assert Counter(asserter._elements_asserters) == Counter(
        [
            DummyAsserter(AsserterFactory, 'some string'),
            DummyAsserter(AsserterFactory, 123),
        ],
    )
    assert asserter.asserter_factory is AsserterFactory


@pytest.mark.parametrize(
    ['expectation', 'object_', 'correct'],
    [
        (set(), None, False),
        (set(), '', True),
        (set(), 'abc', False),
        ({'a', 'b', 'c'}, '', False),
        ({'a', 'b', 'c'}, 'abc', True),
        ({'b', 'c'}, 'abc', False),
        ({'a', 'b'}, 'abc', False),
        ({'a', 'c'}, 'abc', False),
        ({'A', 'b', 'c'}, 'abc', False),
        ({'a', 'B', 'c'}, 'abc', False),
        ({'a', 'b', 'C'}, 'abc', False),
        ({'a', 'b', 'c', 'd'}, 'abc', False),
        ({'a', 'b', 'c'}, 'abcd', False),
        ({'b', 'a', 'c'}, 'abc', True),
        (Unordered([]), None, False),
        (Unordered([]), '', True),
        (Unordered([]), 'abc', False),
        (Unordered(['a', 'b', 'c']), '', False),
        (Unordered(['a', 'b', 'c']), 'abc', True),
        (Unordered(['b', 'c']), 'abc', False),
        (Unordered(['a', 'b']), 'abc', False),
        (Unordered(['a', 'c']), 'abc', False),
        (Unordered(['A', 'b', 'c']), 'abc', False),
        (Unordered(['a', 'B', 'c']), 'abc', False),
        (Unordered(['a', 'b', 'C']), 'abc', False),
        (Unordered(['a', 'b', 'c', 'd']), 'abc', False),
        (Unordered(['a', 'b', 'c']), 'abcd', False),
        (Unordered(['b', 'a', 'c']), 'abc', True),
    ],
)
def test_assert_object(expectation: Any, object_: Any, correct: bool):
    with nullcontext() if correct else pytest.raises(AssertionError):
        UnorderedElementsAsserter(AsserterFactory, expectation).assert_object(object_)
