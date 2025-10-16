from typing import Any
from unittest.mock import MagicMock

import pytest

from panda_pytest_assertions.assert_object import Stringified
from panda_pytest_assertions.assert_object.generators import GeneratorFactory, StringifiedDef
from panda_pytest_assertions.assert_object.generators._generators import StringifiedGenerator


@pytest.mark.parametrize(
    ['definition', 'matches'],
    [
        (StringifiedDef, True),
        (StringifiedDef(), True),
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
    assert StringifiedGenerator.matches(definition) == matches


def test_init():
    definition = MagicMock()
    generator = StringifiedGenerator(GeneratorFactory, definition)

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
@pytest.mark.parametrize('definition', [StringifiedDef, StringifiedDef()])
def test_generate_expectation(definition: Any, object_: Any):
    expectation = StringifiedGenerator(GeneratorFactory, definition).generate_expectation(object_)
    assert isinstance(expectation, Stringified)
    assert expectation.stringified_value == str(object_)
