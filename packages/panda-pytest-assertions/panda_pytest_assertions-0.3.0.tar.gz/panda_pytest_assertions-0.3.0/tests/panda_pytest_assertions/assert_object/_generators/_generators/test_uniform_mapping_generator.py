from contextlib import nullcontext
from typing import Any
from unittest.mock import MagicMock

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object.generators import GeneratorFactory, UniformMappingDef
from panda_pytest_assertions.assert_object.generators._generators import UniformMappingGenerator
from panda_pytest_assertions.assert_object.generators._generators.exceptions import (
    ObjectNotMatchingDefinitionError,
)

from .conftest import DummyExpectation, DummyGenerator


@pytest.mark.parametrize(
    ['definition', 'matches'],
    [
        (UniformMappingDef(object(), object()), True),
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
    assert UniformMappingGenerator.matches(definition) == matches


def test_init():
    definition = UniformMappingDef(
        keys_definition := MagicMock(),
        values_definition := MagicMock(),
    )
    generator = UniformMappingGenerator(GeneratorFactory, definition)

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
    definition = UniformMappingDef(
        keys_definition := MagicMock(),
        values_definition := MagicMock(),
    )

    with nullcontext() if correct else pytest.raises(ObjectNotMatchingDefinitionError):
        expectation = UniformMappingGenerator(GeneratorFactory, definition).generate_expectation(
            object_,
        )

        assert isinstance(expectation, dict)
        assert expectation == {
            DummyExpectation(keys_definition, key): DummyExpectation(values_definition, value)
            for key, value in object_.items()
        }
