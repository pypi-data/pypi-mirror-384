from contextlib import nullcontext
from typing import Any
from unittest.mock import MagicMock

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object import MappingSubset
from panda_pytest_assertions.assert_object.generators import GeneratorFactory, UniformMappingSubsetDef
from panda_pytest_assertions.assert_object.generators._generators import UniformMappingSubsetGenerator
from panda_pytest_assertions.assert_object.generators._generators.exceptions import (
    ObjectNotMatchingDefinitionError,
)

from .conftest import DummyExpectation, DummyGenerator


@pytest.mark.parametrize(
    ['definition', 'matches'],
    [
        (UniformMappingSubsetDef(object(), object()), True),
        (None, False),
        ('string', False),
        (123, False),
        (123.123, False),
        (True, False),
        (False, False),
        ([], False),
        ({}, False),
        (object(), False),
    ],
)
def test_match(definition: Any, matches: bool):
    assert UniformMappingSubsetGenerator.matches(definition) == matches


def test_init():
    definition = UniformMappingSubsetDef(
        keys_definition := MagicMock(),
        values_definition := MagicMock(),
    )
    generator = UniformMappingSubsetGenerator(GeneratorFactory, definition)

    assert generator.keys_generator == DummyGenerator(GeneratorFactory, keys_definition)
    assert generator.values_generator == DummyGenerator(GeneratorFactory, values_definition)
    assert generator.definition == definition
    assert generator.generator_factory is GeneratorFactory


@pytest.mark.parametrize(
    ['object_', 'correct'],
    [
        (
            {
                'attr_1': 'value_1',
                'attr_2': 'value_2',
                'attr_3': 'value_3',
            },
            True,
        ),
        (
            Munch(
                attr_1='value_1',
                attr_2='value_2',
                attr_3='value_3',
            ),
            True,
        ),
        (
            {
                'attr_2': 'value_2',
                'attr_3': 'value_3',
            },
            True,
        ),
        (None, False),
        ('some string', False),
        (123, False),
        (123.321, False),
        (False, False),
    ],
)
def test_generate_expectation(object_: Any, correct: bool):
    definition = UniformMappingSubsetDef(
        keys_definition := MagicMock(),
        values_definition := MagicMock(),
    )

    with nullcontext() if correct else pytest.raises(ObjectNotMatchingDefinitionError):
        expectation = UniformMappingSubsetGenerator(GeneratorFactory, definition).generate_expectation(
            object_,
        )

        assert isinstance(expectation, MappingSubset)
        assert expectation.items_expectations == {
            DummyExpectation(keys_definition, key): DummyExpectation(values_definition, value)
            for key, value in object_.items()
        }
