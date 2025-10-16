from typing import Any
from unittest.mock import MagicMock

import pytest

from panda_pytest_assertions.assert_object.generators import EqualityDef, GeneratorFactory
from panda_pytest_assertions.assert_object.generators._generators import EqualityGenerator


@pytest.mark.parametrize(
    ['definition', 'matches'],
    [
        (EqualityDef, True),
        (EqualityDef(), True),
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
    assert EqualityGenerator.matches(definition) == matches


def test_init():
    definition = MagicMock()
    generator = EqualityGenerator(GeneratorFactory, definition)

    assert generator.definition == definition
    assert generator.generator_factory is GeneratorFactory


@pytest.mark.parametrize(
    'object_',
    [
        None,
        0,
        False,
        'string',
        object(),
        [],
        {},
    ],
)
@pytest.mark.parametrize('definition', [EqualityDef, EqualityDef()])
def test_generate_expectation(definition: Any, object_: Any):
    assert EqualityGenerator(GeneratorFactory, definition).generate_expectation(object_) is object_
