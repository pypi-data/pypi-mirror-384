from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from panda_pytest_assertions.assert_object.generators import (
    generate_expectation,
    Generator,
)


_MODULE = generate_expectation.__module__


@pytest.fixture
def generator() -> MagicMock:
    return MagicMock(name='Generator', spec=Generator)


@pytest.fixture
def generator_factory(generator: MagicMock) -> MagicMock:
    generator_factory = MagicMock(name='generator_factory')
    generator_factory.create.return_value = generator
    return generator_factory


@pytest.fixture
def definition() -> MagicMock:
    return MagicMock(name='definition')


@pytest.fixture
def object_() -> MagicMock:
    return MagicMock(name='object_')


def test_generate_expectation_default_factory(
    mocker: MockerFixture,
    generator: MagicMock,
    definition: MagicMock,
    object_: MagicMock,
):
    create_generator_mock = mocker.patch(
        _MODULE + '.BuiltInGeneratorFactory.create',
        return_value=generator,
    )

    result = generate_expectation(object_, definition)

    create_generator_mock.assert_called_once_with(definition)
    create_generator_mock.return_value.generate_expectation.assert_called_once_with(object_)
    assert result is create_generator_mock.return_value.generate_expectation.return_value


def test_assert_object_custom_factory(
    generator_factory: MagicMock,
    definition: MagicMock,
    object_: MagicMock,
):
    result = generate_expectation(object_, definition, generator_factory=generator_factory)

    generator_factory.create.assert_called_once_with(definition)
    generator_factory.create.return_value.generate_expectation.assert_called_once_with(object_)
    assert result is generator_factory.create.return_value.generate_expectation.return_value
