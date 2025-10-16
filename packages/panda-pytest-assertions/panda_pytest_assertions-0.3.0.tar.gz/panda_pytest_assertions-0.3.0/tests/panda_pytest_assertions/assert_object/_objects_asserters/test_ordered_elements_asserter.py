from contextlib import nullcontext
from typing import Any

import pytest

from panda_pytest_assertions.assert_object import Asserter, AsserterFactory
from panda_pytest_assertions.assert_object._objects_asserters import OrderedElementsAsserter

from .conftest import DummyAsserter


@pytest.mark.parametrize(
    ['expectation', 'matches'],
    [
        (None, False),
        ('string', False),
        (123, False),
        (True, False),
        ([], True),
        ([123, 'abc'], True),
        ((), True),
        ((123,), True),
        ((123, 'abc'), True),
        ({}, False),
        ({'123': '123'}, False),
        ({123: '123'}, False),
        (object(), False),
    ],
)
def test_match(expectation: Any, matches: bool):
    assert OrderedElementsAsserter.matches(expectation) == matches


@pytest.mark.parametrize('expectation_type', [list, tuple])
def test_init(expectation_type: type[list[Any]] | type[tuple[Any, ...]]):
    expectation = expectation_type(
        [
            'some string',
            123,
        ],
    )
    asserter = OrderedElementsAsserter(AsserterFactory, expectation)

    assert asserter._elements_asserters == [
        DummyAsserter(AsserterFactory, 'some string'),
        DummyAsserter(AsserterFactory, 123),
    ]
    assert asserter.asserter_factory is AsserterFactory


@pytest.mark.parametrize(
    ['expectation', 'object_', 'correct'],
    [
        ([], None, False),
        ([], '', True),
        ([], 'abc', False),
        (['a', 'b', 'c'], '', False),
        (['a', 'b', 'c'], 'abc', True),
        (['b', 'c'], 'abc', False),
        (['a', 'b'], 'abc', False),
        (['a', 'c'], 'abc', False),
        (['A', 'b', 'c'], 'abc', False),
        (['a', 'B', 'c'], 'abc', False),
        (['a', 'b', 'C'], 'abc', False),
        (['a', 'b', 'c', 'd'], 'abc', False),
        (['a', 'b', 'c'], 'abcd', False),
        (['b', 'a', 'c'], 'abc', False),
        ((), None, False),
        ((), '', True),
        ((), 'abc', False),
        (('a', 'b', 'c'), '', False),
        (('a', 'b', 'c'), 'abc', True),
        (('b', 'c'), 'abc', False),
        (('a', 'b'), 'abc', False),
        (('a', 'c'), 'abc', False),
        (('A', 'b', 'c'), 'abc', False),
        (('a', 'B', 'c'), 'abc', False),
        (('a', 'b', 'C'), 'abc', False),
        (('a', 'b', 'c', 'd'), 'abc', False),
        (('a', 'b', 'c'), 'abcd', False),
        (('b', 'a', 'c'), 'abc', False),
    ],
)
def test_assert_object(expectation: Any, object_: Any, correct: bool):
    with nullcontext() if correct else pytest.raises(AssertionError):
        OrderedElementsAsserter(AsserterFactory, expectation).assert_object(object_)


def test_inner_assert_object_raises_unknow_excpetion():
    class RaisingAsserter(Asserter):
        def __init__(self, exception_type: type[Exception]) -> None:
            self.exception_type = exception_type

        @classmethod
        def matches(cls, _: Any) -> bool:
            return True

        def assert_object(self, _: Any) -> None:
            msg = 'not raised from zip'
            raise self.exception_type(msg)

    asserter = OrderedElementsAsserter(AsserterFactory, [])
    asserter._elements_asserters = [RaisingAsserter(ValueError)]
    with pytest.raises(ValueError, match='not raised from zip'):
        asserter.assert_object([1])

    asserter._elements_asserters = [RaisingAsserter(ConnectionError)]
    with pytest.raises(ConnectionError, match='not raised from zip'):
        asserter.assert_object([1])
