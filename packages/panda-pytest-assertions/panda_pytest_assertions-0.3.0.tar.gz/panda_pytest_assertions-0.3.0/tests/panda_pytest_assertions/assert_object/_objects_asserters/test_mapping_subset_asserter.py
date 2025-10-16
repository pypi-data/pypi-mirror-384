from contextlib import nullcontext
from typing import Any

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object import AsserterFactory, MappingSubset
from panda_pytest_assertions.assert_object._objects_asserters import MappingSubsetAsserter

from .conftest import DummyAsserter


@pytest.mark.parametrize(
    ['expectation', 'matches'],
    [
        (None, False),
        ('string', False),
        (123, False),
        (True, False),
        ([], False),
        ({}, False),
        ({'123': '123'}, False),
        ({123: '123'}, False),
        (MappingSubset({}), True),
        (MappingSubset({'123': '123'}), True),
        (MappingSubset({123: '123'}), True),
        (object(), False),
    ],
)
def test_match(expectation: Any, matches: bool):
    assert MappingSubsetAsserter.matches(expectation) == matches


def test_init():
    expectation = MappingSubset(
        {
            'attr_1': 'some string',
            'attr_2': 123,
        },
    )
    asserter = MappingSubsetAsserter(AsserterFactory, expectation)

    assert asserter._items_asserters == {
        'attr_1': DummyAsserter(AsserterFactory, 'some string'),
        'attr_2': DummyAsserter(AsserterFactory, 123),
    }
    assert asserter.asserter_factory is AsserterFactory


@pytest.mark.parametrize(
    ['expectation', 'object_', 'correct'],
    [
        (MappingSubset({}), None, False),
        (MappingSubset({}), str.__dict__, True),
        (MappingSubset({'find': str.find}), str, False),
        (MappingSubset({'find': str.find}), str.__dict__, True),
        (MappingSubset({'some': 1}), str.__dict__, False),
        (MappingSubset({'some': 1}), {'some': 1}, True),
        (MappingSubset({'some': 1}), Munch(some=1), True),  # Munch is providing Mapping interface
        (MappingSubset({'some': 1}), {'some': 1, 'other': 1}, True),
        (MappingSubset({'some': 1}), {'some': 2, 'some_else': 1}, False),
        (MappingSubset({'some': 1}), {'some_else': 1}, False),
        (MappingSubset({'some': 1, 'other': 'str'}), {'some': 1}, False),
        (MappingSubset({'some': 1, 'other': 'str'}), {'other': 'str'}, False),
        (MappingSubset({'some': 1, 'other': 'str'}), {'some': 1, 'other': 'hehe'}, False),
        (MappingSubset({'some': 1, 'other': 'str'}), {'some': 3, 'other': 'str'}, False),
        (MappingSubset({'some': 1, 'other': 'str'}), {'some': 'str', 'other': 1}, False),
        (MappingSubset({'some': 1, 'other': 'str'}), {'some': 1, 'other': 'str'}, True),
        (MappingSubset({'some': 1, 'other': 'str'}), {'some': 1, 'other': 'str', 'some_else': 123}, True),
    ],
)
def test_assert_object(expectation: Any, object_: Any, correct: bool):
    with nullcontext() if correct else pytest.raises(AssertionError):
        MappingSubsetAsserter(AsserterFactory, expectation).assert_object(object_)
