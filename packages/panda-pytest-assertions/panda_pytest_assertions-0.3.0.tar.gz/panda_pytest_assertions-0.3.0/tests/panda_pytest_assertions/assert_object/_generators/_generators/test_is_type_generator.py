from typing import Any

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object import IsType
from panda_pytest_assertions.assert_object.generators import GeneratorFactory, IsTypeDef
from panda_pytest_assertions.assert_object.generators._generators import IsTypeGenerator


@pytest.mark.parametrize(
    ['definition', 'matches'],
    [
        (IsTypeDef(), True),
        (IsTypeDef(include_module=True), True),
        (IsTypeDef(include_module=False), True),
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
    assert IsTypeGenerator.matches(definition) == matches


@pytest.mark.parametrize('include_module', [True, False])
def test_init(include_module: bool):
    definition = IsTypeDef(include_module=include_module)
    generator = IsTypeGenerator(GeneratorFactory, definition)

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
    definition = IsTypeDef(
        include_module=include_module,
    )

    expectation = IsTypeGenerator(GeneratorFactory, definition).generate_expectation(object_)

    assert isinstance(expectation, IsType)
    assert expectation.expected_type_name == object_.__class__.__name__
    if include_module:
        assert expectation.expected_type_module == object_.__class__.__module__
    else:
        assert expectation.expected_type_module is None
