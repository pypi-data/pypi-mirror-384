from contextlib import nullcontext
from typing import Any

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object import AsserterFactory
from panda_pytest_assertions.assert_object._objects_asserters import MappingAsserter

from .conftest import DummyAsserter


@pytest.mark.parametrize(
    ['expectation', 'matches'],
    [
        (None, False),
        ('string', False),
        (123, False),
        (True, False),
        ([], False),
        ({}, True),
        ({'123': '123'}, True),
        ({123: '123'}, True),
        (object(), False),
    ],
)
def test_match(expectation: Any, matches: bool):
    assert MappingAsserter.matches(expectation) == matches


def test_init():
    expectation = {
        'attr_1': 'some string',
        'attr_2': 123,
    }
    asserter = MappingAsserter(AsserterFactory, expectation)

    assert asserter._items_asserters == {
        'attr_1': DummyAsserter(AsserterFactory, 'some string'),
        'attr_2': DummyAsserter(AsserterFactory, 123),
    }
    assert asserter.asserter_factory is AsserterFactory


@pytest.mark.parametrize(
    ['expectation', 'object_', 'correct'],
    [
        ({}, None, False),
        ({}, str.__dict__, False),
        ({'find': str.find}, str, False),
        ({'find': str.find}, str.__dict__, False),
        ({'some': 1}, str.__dict__, False),
        ({'some': 1}, {'some': 1}, True),
        ({'some': 1}, Munch(some=1), True),  # Munch is providing Mapping interface
        ({'some': 1}, {'some': 1, 'other': 1}, False),
        ({'some': 1}, {'some': 2, 'some_else': 1}, False),
        ({'some': 1}, {'some_else': 1}, False),
        ({'some': 1, 'other': 'str'}, {'some': 1}, False),
        ({'some': 1, 'other': 'str'}, {'other': 'str'}, False),
        ({'some': 1, 'other': 'str'}, {'some': 1, 'other': 'hehe'}, False),
        ({'some': 1, 'other': 'str'}, {'some': 3, 'other': 'str'}, False),
        ({'some': 1, 'other': 'str'}, {'some': 'str', 'other': 1}, False),
        ({'some': 1, 'other': 'str'}, {'some': 1, 'other': 'str'}, True),
        ({'some': 1, 'other': 'str'}, {'some': 1, 'other': 'str', 'some_else': 123}, False),
    ],
)
def test_assert_object(expectation: Any, object_: Any, correct: bool):
    with nullcontext() if correct else pytest.raises(AssertionError):
        MappingAsserter(AsserterFactory, expectation).assert_object(object_)
