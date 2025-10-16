from collections import deque
from typing import Any

import pytest
from pytest_mock import MockerFixture

from panda_pytest_assertions.assert_object.generators import Generator, GeneratorFactory


class DummyGenerator(Generator):
    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        _ = definition
        return True

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, DummyGenerator)
            and self.definition == value.definition
            and self.generator_factory is value.generator_factory
        )

    def __hash__(self) -> int:
        return hash(str(self))

    def generate_expectation(self, object_: Any) -> Any:  # noqa: ANN401
        return DummyExpectation(self.definition, object_)

    def __str__(self) -> str:
        return f'DummyGenerator({self.definition}, {self.generator_factory})'

    def __repr__(self) -> str:
        return str(self)


class DummyExpectation:
    def __init__(self, definition: Any, object_: Any) -> None:  # noqa: ANN401
        self.definition = definition
        self.object_ = object_

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, DummyExpectation)
            and self.definition == value.definition
            and self.object_ == value.object_
        )

    def __hash__(self) -> int:
        return hash(str(self))

    def __str__(self) -> str:
        return f'DummyGenerator({self.definition}, {self.object_})'

    def __repr__(self) -> str:
        return str(self)


@pytest.fixture(autouse=True)
def _(mocker: MockerFixture) -> None:
    mocker.patch.object(GeneratorFactory, '_GENERATOR_TYPES', deque())
    GeneratorFactory.register_generator(DummyGenerator)
