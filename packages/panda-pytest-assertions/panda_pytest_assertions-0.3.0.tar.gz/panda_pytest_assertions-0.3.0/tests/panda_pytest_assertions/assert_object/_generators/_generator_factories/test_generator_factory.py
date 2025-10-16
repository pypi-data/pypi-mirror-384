from collections import deque
from typing import Any

import pytest
from pytest_mock import MockerFixture

from panda_pytest_assertions.assert_object import GeneratorFactoryProtocol
from panda_pytest_assertions.assert_object.generators import GeneratorFactory


@pytest.fixture(autouse=True)
def _(mocker: MockerFixture) -> None:
    """
    Make sure that the test does not modify built-in class var.

    :param mocker: mocker
    """
    mocker.patch.object(GeneratorFactory, '_GENERATOR_TYPES', deque())


class DummyGenerator:
    def __init__(self, generator_factory: type[GeneratorFactoryProtocol], definition: Any) -> None:
        self.generator_factory = generator_factory
        self.definition = definition

    @classmethod
    def matches(cls, definition: Any) -> bool:
        _ = definition
        return True

    def generate_expectation(self, object_: Any) -> None: ...


class InceptGenerator(DummyGenerator):
    @classmethod
    def matches(cls, definition: Any) -> bool:
        return isinstance(definition, str) and definition.startswith('incept')


class InceptionGenerator(DummyGenerator):
    @classmethod
    def matches(cls, definition: Any) -> bool:
        return isinstance(definition, str) and definition.startswith('inception')


class IntGenerator(DummyGenerator):
    @classmethod
    def matches(cls, definition: Any) -> bool:
        return isinstance(definition, int)


class TupleGenerator(DummyGenerator):
    @classmethod
    def matches(cls, definition: Any) -> bool:
        return isinstance(definition, tuple)


class StrGenerator(DummyGenerator):
    @classmethod
    def matches(cls, definition: Any) -> bool:
        return isinstance(definition, str)


def test_create():
    GeneratorFactory.register_generator(InceptGenerator)
    GeneratorFactory.register_generator(InceptionGenerator)
    assert list(GeneratorFactory._GENERATOR_TYPES) == [InceptionGenerator, InceptGenerator]

    generator = GeneratorFactory.create('incept')
    assert isinstance(generator, InceptGenerator)
    assert generator.definition == 'incept'

    generator = GeneratorFactory.create('inceptNOTion')
    assert isinstance(generator, InceptGenerator)
    assert generator.definition == 'inceptNOTion'

    generator = GeneratorFactory.create('inception')
    assert isinstance(generator, InceptionGenerator)
    assert generator.definition == 'inception'

    with pytest.raises(ValueError, match='None of the registered'):
        GeneratorFactory.create('incep')

    with pytest.raises(ValueError, match='None of the registered'):
        GeneratorFactory.create(123)

    GeneratorFactory.register_generator(IntGenerator)

    generator = GeneratorFactory.create(123)
    assert isinstance(generator, IntGenerator)
    assert generator.definition == 123


def test_register_generator():
    assert list(GeneratorFactory._GENERATOR_TYPES) == []

    GeneratorFactory.register_generator(InceptGenerator)
    assert list(GeneratorFactory._GENERATOR_TYPES) == [InceptGenerator]

    GeneratorFactory.register_generator(InceptionGenerator, after=InceptGenerator)
    assert list(GeneratorFactory._GENERATOR_TYPES) == [InceptGenerator, InceptionGenerator]

    GeneratorFactory.register_generator(TupleGenerator, before=InceptionGenerator)
    assert list(GeneratorFactory._GENERATOR_TYPES) == [TupleGenerator, InceptGenerator, InceptionGenerator]

    GeneratorFactory.register_generator(IntGenerator, after=TupleGenerator, before=InceptionGenerator)
    assert list(GeneratorFactory._GENERATOR_TYPES) == [
        TupleGenerator,
        IntGenerator,
        InceptGenerator,
        InceptionGenerator,
    ]

    with pytest.raises(ValueError, match='Cannot register'):
        GeneratorFactory.register_generator(StrGenerator, after=InceptGenerator, before=IntGenerator)
    assert list(GeneratorFactory._GENERATOR_TYPES) == [
        TupleGenerator,
        IntGenerator,
        InceptGenerator,
        InceptionGenerator,
    ]


def test_custom_base_class():
    class CustomGeneratorFactory(GeneratorFactory): ...

    assert GeneratorFactory._GENERATOR_TYPES is CustomGeneratorFactory._GENERATOR_TYPES
    CustomGeneratorFactory.register_generator(DummyGenerator)
    assert GeneratorFactory._GENERATOR_TYPES is not CustomGeneratorFactory._GENERATOR_TYPES

    assert DummyGenerator not in GeneratorFactory._GENERATOR_TYPES
    assert DummyGenerator in CustomGeneratorFactory._GENERATOR_TYPES

    with pytest.raises(ValueError, match='None of the registered generators matches definition'):
        GeneratorFactory.create('some primitive')

    expectation = CustomGeneratorFactory.create('some primitive')
    assert isinstance(expectation, DummyGenerator)
    assert expectation.generator_factory is CustomGeneratorFactory
    assert expectation.definition == 'some primitive'
