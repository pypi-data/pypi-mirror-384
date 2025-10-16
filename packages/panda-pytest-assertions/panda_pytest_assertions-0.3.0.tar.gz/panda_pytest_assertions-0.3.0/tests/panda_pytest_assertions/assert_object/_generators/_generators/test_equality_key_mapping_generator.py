from contextlib import nullcontext
from typing import Any
from unittest.mock import MagicMock

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object.generators import GeneratorFactory
from panda_pytest_assertions.assert_object.generators._generators import EqualityKeyMappingGenerator
from panda_pytest_assertions.assert_object.generators._generators.exceptions import (
    ObjectNotMatchingDefinitionError,
)

from .conftest import DummyExpectation, DummyGenerator


@pytest.mark.parametrize(
    ['definition', 'matches'],
    [
        (None, False),
        ('string', False),
        (123, False),
        (123.123, False),
        (True, False),
        (False, False),
        ([], False),
        ({}, True),
        (object(), False),
    ],
)
def test_match(definition: Any, matches: bool):
    assert EqualityKeyMappingGenerator.matches(definition) == matches


def test_init():
    definition = {
        'attr_1': 'some string',
        'attr_2': 123,
    }
    generator = EqualityKeyMappingGenerator(GeneratorFactory, definition)

    assert generator.items_generators == {
        'attr_1': DummyGenerator(GeneratorFactory, 'some string'),
        'attr_2': DummyGenerator(GeneratorFactory, 123),
    }
    assert generator.definition == definition
    assert generator.generator_factory is GeneratorFactory


@pytest.mark.parametrize(
    ['object_', 'correct'],
    [
        (
            {
                'attr_1': 'value_1',
                'attr_2': 'value_2',
            },
            True,
        ),
        (
            Munch(
                attr_1='value_1',
                attr_2='value_2',
            ),
            True,
        ),
        (
            {
                'attr_1': 'value_1',
                'attr_2': 'value_2',
                'attr_3': 'value_3',
            },
            False,
        ),
        (
            Munch(
                attr_1='value_1',
                attr_2='value_2',
                attr_3='value_3',
            ),
            False,
        ),
        (
            {
                'attr_2': 'value_2',
            },
            False,
        ),
        (None, False),
        ('some string', False),
        (123, False),
        (123.321, False),
        (False, False),
    ],
)
def test_generate_expectation(object_: Any, correct: bool):
    definition = {
        'attr_1': (attr_1_definition := MagicMock()),
        'attr_2': (attr_2_definition := MagicMock()),
    }

    with nullcontext() if correct else pytest.raises(ObjectNotMatchingDefinitionError):
        expectation = EqualityKeyMappingGenerator(GeneratorFactory, definition).generate_expectation(object_)

        assert isinstance(expectation, dict)
        assert expectation == {
            'attr_1': DummyExpectation(
                attr_1_definition,
                object_['attr_1'],
            ),
            'attr_2': DummyExpectation(
                attr_2_definition,
                object_['attr_2'],
            ),
        }
