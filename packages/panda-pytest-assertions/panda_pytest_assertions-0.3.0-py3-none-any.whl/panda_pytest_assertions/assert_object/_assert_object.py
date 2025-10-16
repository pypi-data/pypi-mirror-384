from typing import Any

from ._asserter_factories import BuiltInAsserterFactory
from ._protocols import AsserterFactoryProtocol


def assert_object(
    expectation: Any,  # noqa: ANN401
    object_: Any,  # noqa: ANN401
    *,
    asserter_factory: type[AsserterFactoryProtocol] = BuiltInAsserterFactory,
) -> None:
    asserter = asserter_factory.create(expectation)
    try:
        asserter.assert_object(object_)
    except AssertionError as exc:
        msg = f'Object assertion failed. {exc!s}'
        raise AssertionError(msg) from None


class Expectation:  # noqa: PLW1641
    def __init__(
        self,
        expectation: Any,  # noqa: ANN401
        *,
        asserter_factory: type[AsserterFactoryProtocol] = BuiltInAsserterFactory,
    ) -> None:
        self.expectation = expectation
        self.asserter_factory = asserter_factory

    def __eq__(self, value: object) -> bool:
        try:
            assert_object(self.expectation, value, asserter_factory=self.asserter_factory)
        except AssertionError:
            return False
        return True
