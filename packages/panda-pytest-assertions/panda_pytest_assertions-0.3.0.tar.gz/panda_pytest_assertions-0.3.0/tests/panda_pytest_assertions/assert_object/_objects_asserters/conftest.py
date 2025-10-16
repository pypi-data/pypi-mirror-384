from collections import deque
from typing import Any

import pytest
from pytest_mock import MockerFixture

from panda_pytest_assertions.assert_object import Asserter, AsserterFactory


class DummyAsserter(Asserter):
    @classmethod
    def matches(cls, expectation: Any) -> bool:  # noqa: ANN401
        _ = expectation
        return True

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, DummyAsserter)
            and self.expectation == value.expectation
            and self.asserter_factory is value.asserter_factory
        )

    def __hash__(self) -> int:
        return hash(str(self))

    def assert_object(self, object_: Any) -> None:  # noqa: ANN401
        assert self.expectation == object_

    def __str__(self) -> str:
        return f'DummyAsserter({self.expectation}, {self.asserter_factory})'

    def __repr__(self) -> str:
        return str(self)


@pytest.fixture(autouse=True)
def _(mocker: MockerFixture) -> None:
    mocker.patch.object(AsserterFactory, '_ASSERTER_TYPES', deque())
    AsserterFactory.register_asserter(DummyAsserter)
