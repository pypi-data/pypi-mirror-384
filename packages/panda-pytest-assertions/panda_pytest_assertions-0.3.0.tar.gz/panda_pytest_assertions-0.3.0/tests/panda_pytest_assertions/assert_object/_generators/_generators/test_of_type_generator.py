from collections.abc import Mapping
from contextlib import nullcontext
from types import NoneType
from typing import Any
from unittest.mock import MagicMock

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object.generators import GeneratorFactory, OfTypeDef
from panda_pytest_assertions.assert_object.generators._generators import OfTypeGenerator
from panda_pytest_assertions.assert_object.generators._generators.exceptions import (
    ObjectNotMatchingDefinitionError,
)

from .conftest import DummyExpectation, DummyGenerator


@pytest.mark.parametrize(
    ['definition', 'matches'],
    [
        (OfTypeDef(str, object()), True),
        (OfTypeDef(int, object()), True),
        (OfTypeDef(object, object()), True),
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
    assert OfTypeGenerator.matches(definition) == matches


@pytest.mark.parametrize('expected_type', [str, int, object, None])
def test_init(expected_type: type[Any] | None):
    definition = OfTypeDef(
        expected_type,
        object_definition := MagicMock(),
    )
    generator = OfTypeGenerator(GeneratorFactory, definition)
    if expected_type is None:
        expected_type = NoneType
    assert generator.object_generator == DummyGenerator(GeneratorFactory, object_definition)
    assert generator.definition == definition
    assert generator.expected_type == expected_type
    assert generator.generator_factory is GeneratorFactory


@pytest.mark.parametrize(
    ['expected_type', 'object_', 'correct'],
    [
        (Mapping, {'attr_1': 'value_1'}, True),
        (Munch, {'attr_1': 'value_1'}, False),
        (dict, {'attr_1': 'value_1'}, True),
        (Mapping, Munch(attr_1='value_1'), True),
        (Munch, Munch(attr_1='value_1'), True),
        (dict, Munch(attr_1='value_1'), True),
        (NoneType, None, True),
        (None, None, True),
        (str, 'some', True),
        (int, 'some', False),
        (str, 123, False),
        (int, 123, True),
        (str, False, False),
        (int, False, True),
        (bool, False, True),
    ],
)
def test_generate_expectation(
    object_: Any,
    expected_type: type[Any],
    correct: bool,
):
    definition = OfTypeDef(
        expected_type,
        object_definition := MagicMock(),
    )
    with nullcontext() if correct else pytest.raises(ObjectNotMatchingDefinitionError):
        expectation = OfTypeGenerator(GeneratorFactory, definition).generate_expectation(object_)

        assert expectation == DummyExpectation(object_definition, object_)
