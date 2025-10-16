from contextlib import nullcontext
from typing import Any, Literal
from unittest.mock import MagicMock

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object.generators import GeneratorFactory
from panda_pytest_assertions.assert_object.generators._generators import OrderedGenerator
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
        ([], True),
        ((), True),
        ({}, False),
        (object(), False),
    ],
)
def test_match(definition: Any, matches: bool):
    assert OrderedGenerator.matches(definition) == matches


@pytest.mark.parametrize('expectation_type', [list, tuple])
def test_init(expectation_type: type[Any]):
    definition = expectation_type(
        (
            element_1_definition := MagicMock(),
            element_2_definition := MagicMock(),
            element_3_definition := MagicMock(),
        ),
    )
    generator = OrderedGenerator(GeneratorFactory, definition)

    assert generator.elements_generators == [
        DummyGenerator(GeneratorFactory, element_1_definition),
        DummyGenerator(GeneratorFactory, element_2_definition),
        DummyGenerator(GeneratorFactory, element_3_definition),
    ]
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
        ('som', ['s', 'o', 'm']),
        ('some', False),
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
    definition = expectation_type(
        (
            element_1_definition := MagicMock(),
            element_2_definition := MagicMock(),
            element_3_definition := MagicMock(),
        ),
    )

    with nullcontext() if expected_elements is not False else pytest.raises(ObjectNotMatchingDefinitionError):
        expectation = OrderedGenerator(GeneratorFactory, definition).generate_expectation(object_)

        assert isinstance(expectation, expectation_type)
        assert list(expectation) == [
            DummyExpectation(element_1_definition, expected_elements[0]),  # type: ignore [index]
            DummyExpectation(element_2_definition, expected_elements[1]),  # type: ignore [index]
            DummyExpectation(element_3_definition, expected_elements[2]),  # type: ignore [index]
        ]
