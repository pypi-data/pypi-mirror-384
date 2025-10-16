from contextlib import nullcontext
from typing import Any

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object import AsserterFactory, ObjectAttributes
from panda_pytest_assertions.assert_object._objects_asserters import ObjectAttributesAsserter

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
        (ObjectAttributes({}), True),
        (ObjectAttributes({'123': '123'}), True),
        (object(), False),
    ],
)
def test_match(expectation: Any, matches: bool):
    assert ObjectAttributesAsserter.matches(expectation) == matches


def test_init():
    expectation = ObjectAttributes(
        {
            'attr_1': 'some string',
            'attr_2': 123,
        },
    )
    asserter = ObjectAttributesAsserter(AsserterFactory, expectation)

    assert asserter._attributes_asserters == {
        'attr_1': DummyAsserter(AsserterFactory, 'some string'),
        'attr_2': DummyAsserter(AsserterFactory, 123),
    }
    assert asserter.asserter_factory is AsserterFactory


@pytest.mark.parametrize(
    ['expectation', 'object_', 'correct'],
    [
        (ObjectAttributes({}), None, True),
        (ObjectAttributes({'some': 1}), None, False),
        (ObjectAttributes({'__hash__': None.__hash__}), None, True),
        (ObjectAttributes({'find': str.find}), str, True),
        (ObjectAttributes({'some': 1}), {'some': 1}, False),
        (ObjectAttributes({'some': 1}), Munch(some=1), True),
        (ObjectAttributes({'some': 1}), Munch(some=1, other=1), True),
        (ObjectAttributes({'some': 1}), Munch(some=2, some_else=1), False),
        (ObjectAttributes({'some': 1}), Munch(some_else=1), False),
        (ObjectAttributes({'some': 1, 'other': 'str'}), Munch(some=1), False),
        (ObjectAttributes({'some': 1, 'other': 'str'}), Munch(other='str'), False),
        (ObjectAttributes({'some': 1, 'other': 'str'}), Munch(some=1, other='hehe'), False),
        (ObjectAttributes({'some': 1, 'other': 'str'}), Munch(some=3, other='str'), False),
        (ObjectAttributes({'some': 1, 'other': 'str'}), Munch(some='str', other=1), False),
        (ObjectAttributes({'some': 1, 'other': 'str'}), Munch(some=1, other='str'), True),
        (ObjectAttributes({'some': 1, 'other': 'str'}), Munch(some=1, other='str', some_else=123), True),
    ],
)
def test_assert_object(expectation: Any, object_: Any, correct: bool):
    with nullcontext() if correct else pytest.raises(AssertionError):
        ObjectAttributesAsserter(AsserterFactory, expectation).assert_object(object_)
