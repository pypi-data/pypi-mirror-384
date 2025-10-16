from contextlib import nullcontext
from typing import Any, Literal
from unittest.mock import MagicMock

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object import Unordered
from panda_pytest_assertions.assert_object.generators import GeneratorFactory, UniformUnorderedDef
from panda_pytest_assertions.assert_object.generators._generators import UnorderedGenerator
from panda_pytest_assertions.assert_object.generators._generators.exceptions import (
    ObjectNotMatchingDefinitionError,
)

from .conftest import DummyExpectation, DummyGenerator


@pytest.mark.parametrize(
    ['definition', 'matches'],
    [
        (UniformUnorderedDef(object()), True),
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
    assert UnorderedGenerator.matches(definition) == matches


def test_init():
    definition = UniformUnorderedDef(
        elements_definition := MagicMock(),
    )
    generator = UnorderedGenerator(GeneratorFactory, definition)

    assert generator.elements_generator == DummyGenerator(GeneratorFactory, elements_definition)
    assert generator.definition == definition
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
def test_generate_expectation(
    object_: Any,
    expected_elements: list[str] | Literal[False],
):
    definition = UniformUnorderedDef(
        elements_definition := MagicMock(),
    )

    with nullcontext() if expected_elements is not False else pytest.raises(ObjectNotMatchingDefinitionError):
        expectation = UnorderedGenerator(GeneratorFactory, definition).generate_expectation(object_)

        assert isinstance(expectation, Unordered)
        assert expectation.elements_expectations == [
            DummyExpectation(elements_definition, element)
            for element in expected_elements  # type: ignore [union-attr]
        ]
