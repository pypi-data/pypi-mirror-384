from contextlib import nullcontext
from typing import Any, Literal
from unittest.mock import MagicMock

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object.generators import GeneratorFactory, UniformOrderedDef
from panda_pytest_assertions.assert_object.generators._generators import UniformOrderedGenerator
from panda_pytest_assertions.assert_object.generators._generators.exceptions import (
    ObjectNotMatchingDefinitionError,
)

from .conftest import DummyExpectation, DummyGenerator


@pytest.mark.parametrize(
    ['definition', 'matches'],
    [
        (UniformOrderedDef(object()), True),
        (UniformOrderedDef(object(), expectation_type=list), True),
        (UniformOrderedDef(object(), expectation_type=tuple), True),
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
    assert UniformOrderedGenerator.matches(definition) == matches


@pytest.mark.parametrize('expectation_type', [list, tuple])
def test_init(expectation_type: type[Any]):
    definition = UniformOrderedDef(
        elements_definition := MagicMock(),
        expectation_type=expectation_type,
    )
    generator = UniformOrderedGenerator(GeneratorFactory, definition)

    assert generator.elements_generator == DummyGenerator(GeneratorFactory, elements_definition)
    assert generator.definition == definition
    assert generator.expectation_type == expectation_type
    assert generator.generator_factory is GeneratorFactory


@pytest.mark.parametrize(
    ['object_', 'expected_elements'],
    [
        (
            {
                'attr_1': 'value_1',
                'attr_2': 'value_2',
                'attr_3': 'value_3',
            },
            ['attr_1', 'attr_2', 'attr_3'],
        ),
        (
            Munch(
                attr_1='value_1',
                attr_2='value_2',
                attr_3='value_3',
            ),
            ['attr_1', 'attr_2', 'attr_3'],
        ),
        (None, False),
        ('some', ['s', 'o', 'm', 'e']),
        (123, False),
        (123.321, False),
        (False, False),
    ],
)
@pytest.mark.parametrize('expectation_type', [list, tuple])
def test_generate_expectation(
    object_: Any,
    expected_elements: list[str] | Literal[False],
    expectation_type: type[Any],
):
    definition = UniformOrderedDef(
        elements_definition := MagicMock(),
        expectation_type=expectation_type,
    )

    with nullcontext() if expected_elements is not False else pytest.raises(ObjectNotMatchingDefinitionError):
        expectation = UniformOrderedGenerator(GeneratorFactory, definition).generate_expectation(object_)

        assert isinstance(expectation, expectation_type)
        assert list(expectation) == [
            DummyExpectation(elements_definition, element)
            for element in expected_elements  # type: ignore [union-attr]
        ]
