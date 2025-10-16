from typing import Any
from unittest.mock import MagicMock

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object import WithType
from panda_pytest_assertions.assert_object.generators import GeneratorFactory, WithTypeDef
from panda_pytest_assertions.assert_object.generators._generators import WithTypeGenerator

from .conftest import DummyExpectation, DummyGenerator


@pytest.mark.parametrize(
    ['definition', 'matches'],
    [
        (WithTypeDef(object()), True),
        (WithTypeDef(object(), include_module=True), True),
        (WithTypeDef(object(), include_module=False), True),
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
    assert WithTypeGenerator.matches(definition) == matches


@pytest.mark.parametrize('include_module', [True, False])
def test_init(include_module: bool):
    definition = WithTypeDef(
        object_definition := MagicMock(),
        include_module=include_module,
    )
    generator = WithTypeGenerator(GeneratorFactory, definition)

    assert generator.object_generator == DummyGenerator(GeneratorFactory, object_definition)
    assert generator.definition == definition
    assert generator.include_module == include_module
    assert generator.generator_factory is GeneratorFactory


@pytest.mark.parametrize(
    'object_',
    [
        {
            'attr_1': 'value_1',
            'attr_2': 'value_2',
            'attr_3': 'value_3',
        },
        Munch(
            attr_1='value_1',
            attr_2='value_2',
            attr_3='value_3',
        ),
        None,
        'some',
        123,
        123.321,
        False,
    ],
)
@pytest.mark.parametrize('include_module', [True, False])
def test_generate_expectation(
    object_: Any,
    include_module: bool,
):
    definition = WithTypeDef(
        elements_definition := MagicMock(),
        include_module=include_module,
    )

    expectation = WithTypeGenerator(GeneratorFactory, definition).generate_expectation(object_)

    assert isinstance(expectation, WithType)
    assert expectation.expectation == DummyExpectation(elements_definition, object_)
    assert expectation.expected_type_name == object_.__class__.__name__
    if include_module:
        assert expectation.expected_type_module == object_.__class__.__module__
    else:
        assert expectation.expected_type_module is None
