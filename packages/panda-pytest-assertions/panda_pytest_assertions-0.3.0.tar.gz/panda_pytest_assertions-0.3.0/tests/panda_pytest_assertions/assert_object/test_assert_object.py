from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from panda_pytest_assertions.assert_object import assert_object, Asserter, Expectation
from panda_pytest_assertions.assert_object._asserter_factories.built_in_asserter_factory import (
    BuiltInAsserterFactory,
)


_MODULE = assert_object.__module__


@pytest.fixture
def asserter() -> MagicMock:
    return MagicMock(name='Asserter', spec=Asserter)


@pytest.fixture
def asserter_factory(asserter: MagicMock) -> MagicMock:
    asserter_factory = MagicMock(name='asserter_factory')
    asserter_factory.create.return_value = asserter
    return asserter_factory


@pytest.fixture
def expectation() -> MagicMock:
    return MagicMock(name='expectation')


@pytest.fixture
def object_() -> MagicMock:
    return MagicMock(name='object_')


def test_assert_object_default_factory(
    mocker: MockerFixture,
    asserter: MagicMock,
    expectation: MagicMock,
    object_: MagicMock,
):
    create_asserter_mock = mocker.patch(
        _MODULE + '.BuiltInAsserterFactory.create',
        return_value=asserter,
    )

    assert_object(expectation, object_)

    create_asserter_mock.assert_called_once_with(expectation)
    create_asserter_mock.return_value.assert_object.assert_called_once_with(object_)


def test_assert_object_custom_factory(
    asserter_factory: MagicMock,
    expectation: MagicMock,
    object_: MagicMock,
):
    assert_object(expectation, object_, asserter_factory=asserter_factory)

    asserter_factory.create.assert_called_once_with(expectation)
    asserter_factory.create.return_value.assert_object.assert_called_once_with(object_)


def test_assert_object_assertion_error(
    asserter_factory: MagicMock,
    asserter: MagicMock,
    expectation: MagicMock,
    object_: MagicMock,
):
    asserter.assert_object.side_effect = AssertionError('Oh NO!')

    with pytest.raises(AssertionError, match=r'Object assertion failed. Oh NO!'):
        assert_object(expectation, object_, asserter_factory=asserter_factory)


def test_assert_object_other_error(
    asserter_factory: MagicMock,
    asserter: MagicMock,
    expectation: MagicMock,
    object_: MagicMock,
):
    asserter.assert_object.side_effect = ConnectionError

    with pytest.raises(ConnectionError):
        assert_object(expectation, object_, asserter_factory=asserter_factory)


@pytest.mark.parametrize('use_default_factory', [True, False])
def test_expectation(
    mocker: MockerFixture,
    asserter_factory: MagicMock | type[BuiltInAsserterFactory],
    use_default_factory: bool,
    expectation: MagicMock,
):
    if use_default_factory:
        asserter_factory = BuiltInAsserterFactory
    assert_object_mock = mocker.patch(_MODULE + '.assert_object')

    instance = (
        Expectation(expectation)
        if use_default_factory
        else Expectation(expectation, asserter_factory=asserter_factory)
    )
    assert instance.expectation is expectation

    assert instance == (value := 'ANYTHING')
    assert_object_mock.assert_called_once_with(expectation, value, asserter_factory=asserter_factory)

    assert_object_mock.reset_mock()
    assert_object_mock.side_effect = AssertionError
    assert instance != (value := 'ANYTHING')
    assert_object_mock.assert_called_once_with(expectation, value, asserter_factory=asserter_factory)

    assert_object_mock.reset_mock()
    assert_object_mock.side_effect = Exception
    with pytest.raises(Exception):  # noqa: B017, PT011
        instance != (value := 'ANYTHING')  # noqa: B015
    assert_object_mock.assert_called_once_with(expectation, value, asserter_factory=asserter_factory)
