from contextlib import nullcontext
from types import NoneType
from typing import Any, Literal
from unittest.mock import MagicMock

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object.generators import GeneratorFactory, UnionDef
from panda_pytest_assertions.assert_object.generators._generators import UnionGenerator
from panda_pytest_assertions.assert_object.generators._generators.exceptions import (
    ObjectNotMatchingDefinitionError,
)

from .conftest import DummyExpectation, DummyGenerator


@pytest.mark.parametrize(
    ['definition', 'matches'],
    [
        (UnionDef(object(), object(), object()), True),
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
    assert UnionGenerator.matches(definition) == matches


def test_init():
    definition = UnionDef(
        definition_1 := MagicMock(),
        definition_2 := MagicMock(),
        definition_3 := MagicMock(),
    )
    generator = UnionGenerator(GeneratorFactory, definition)

    assert generator.generators == (
        DummyGenerator(GeneratorFactory, definition_1),
        DummyGenerator(GeneratorFactory, definition_2),
        DummyGenerator(GeneratorFactory, definition_3),
    )
    assert generator.definition == definition
    assert generator.generator_factory is GeneratorFactory


@pytest.mark.parametrize(
    ['object_', 'chosen_definition'],
    [
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
        (None, NoneType),
        ('some', str),
        (123, int),
        (123.321, False),
        (False, int),
    ],
)
def test_generate_expectation(
    object_: Any,
    chosen_definition: type[str] | type[int] | Literal[False],
):
    class TypeMatchingGenerator(DummyGenerator):
        def generate_expectation(self, object_: Any) -> Any:
            if not isinstance(object_, self.definition):
                raise ObjectNotMatchingDefinitionError
            return DummyExpectation(self.definition, object_)

    GeneratorFactory._GENERATOR_TYPES.clear()
    GeneratorFactory.register_generator(TypeMatchingGenerator)
    definition = UnionDef(str, int, bool, NoneType)

    with nullcontext() if chosen_definition is not False else pytest.raises(ObjectNotMatchingDefinitionError):
        expectation = UnionGenerator(GeneratorFactory, definition).generate_expectation(object_)

        assert expectation == DummyExpectation(chosen_definition, object_)
