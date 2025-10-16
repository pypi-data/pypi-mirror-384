from collections import deque
from typing import Any

import pytest
from pytest_mock import MockerFixture

from panda_pytest_assertions.assert_object import AsserterFactory, AsserterFactoryProtocol


@pytest.fixture(autouse=True)
def _(mocker: MockerFixture) -> None:
    """
    Make sure that the test does not modify built-in class var.

    :param mocker: mocker
    """
    mocker.patch.object(AsserterFactory, '_ASSERTER_TYPES', deque())


class DummyAsserter:
    def __init__(self, asserter_factory: type[AsserterFactoryProtocol], expectation: Any) -> None:
        self.asserter_factory = asserter_factory
        self.expectation = expectation

    @classmethod
    def matches(cls, expectation: Any) -> bool:
        _ = expectation
        return True

    def assert_object(self, object_: Any) -> None: ...


class InceptAsserter(DummyAsserter):
    @classmethod
    def matches(cls, expectation: Any) -> bool:
        return isinstance(expectation, str) and expectation.startswith('incept')


class InceptionAsserter(DummyAsserter):
    @classmethod
    def matches(cls, expectation: Any) -> bool:
        return isinstance(expectation, str) and expectation.startswith('inception')


class IntAsserter(DummyAsserter):
    @classmethod
    def matches(cls, expectation: Any) -> bool:
        return isinstance(expectation, int)


class TupleAsserter(DummyAsserter):
    @classmethod
    def matches(cls, expectation: Any) -> bool:
        return isinstance(expectation, tuple)


class StrAsserter(DummyAsserter):
    @classmethod
    def matches(cls, expectation: Any) -> bool:
        return isinstance(expectation, str)


def test_create():
    AsserterFactory.register_asserter(InceptAsserter)
    AsserterFactory.register_asserter(InceptionAsserter)
    assert list(AsserterFactory._ASSERTER_TYPES) == [InceptionAsserter, InceptAsserter]

    asserter = AsserterFactory.create('incept')
    assert isinstance(asserter, InceptAsserter)
    assert asserter.expectation == 'incept'

    asserter = AsserterFactory.create('inceptNOTion')
    assert isinstance(asserter, InceptAsserter)
    assert asserter.expectation == 'inceptNOTion'

    asserter = AsserterFactory.create('inception')
    assert isinstance(asserter, InceptionAsserter)
    assert asserter.expectation == 'inception'

    with pytest.raises(ValueError, match='None of the registered'):
        AsserterFactory.create('incep')

    with pytest.raises(ValueError, match='None of the registered'):
        AsserterFactory.create(123)

    AsserterFactory.register_asserter(IntAsserter)

    asserter = AsserterFactory.create(123)
    assert isinstance(asserter, IntAsserter)
    assert asserter.expectation == 123


def test_register_asserter():
    assert list(AsserterFactory._ASSERTER_TYPES) == []

    AsserterFactory.register_asserter(InceptAsserter)
    assert list(AsserterFactory._ASSERTER_TYPES) == [InceptAsserter]

    AsserterFactory.register_asserter(InceptionAsserter, after=InceptAsserter)
    assert list(AsserterFactory._ASSERTER_TYPES) == [InceptAsserter, InceptionAsserter]

    AsserterFactory.register_asserter(TupleAsserter, before=InceptionAsserter)
    assert list(AsserterFactory._ASSERTER_TYPES) == [TupleAsserter, InceptAsserter, InceptionAsserter]

    AsserterFactory.register_asserter(IntAsserter, after=TupleAsserter, before=InceptionAsserter)
    assert list(AsserterFactory._ASSERTER_TYPES) == [
        TupleAsserter,
        IntAsserter,
        InceptAsserter,
        InceptionAsserter,
    ]

    with pytest.raises(ValueError, match='Cannot register'):
        AsserterFactory.register_asserter(StrAsserter, after=InceptAsserter, before=IntAsserter)
    assert list(AsserterFactory._ASSERTER_TYPES) == [
        TupleAsserter,
        IntAsserter,
        InceptAsserter,
        InceptionAsserter,
    ]


def test_custom_base_class():
    class CustomAsserterFactory(AsserterFactory): ...

    assert AsserterFactory._ASSERTER_TYPES is CustomAsserterFactory._ASSERTER_TYPES
    CustomAsserterFactory.register_asserter(DummyAsserter)
    assert AsserterFactory._ASSERTER_TYPES is not CustomAsserterFactory._ASSERTER_TYPES

    assert DummyAsserter not in AsserterFactory._ASSERTER_TYPES
    assert DummyAsserter in CustomAsserterFactory._ASSERTER_TYPES

    with pytest.raises(ValueError, match='None of the registered asserters matches expectation'):
        AsserterFactory.create('some primitive')

    expectation = CustomAsserterFactory.create('some primitive')
    assert isinstance(expectation, DummyAsserter)
    assert expectation.asserter_factory is CustomAsserterFactory
    assert expectation.expectation == 'some primitive'
