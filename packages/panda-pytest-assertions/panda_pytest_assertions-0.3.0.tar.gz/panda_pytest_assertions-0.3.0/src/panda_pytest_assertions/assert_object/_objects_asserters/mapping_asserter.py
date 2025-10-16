from collections.abc import Mapping
from typing import Any

from panda_pytest_assertions.assert_object._protocols import AsserterFactoryProtocol

from .asserter import Asserter


class MappingAsserter(Asserter):
    """
    Assert mapping items fulfill expectations defined in another mapping.

    Expectation is a mapping between object keys and coresponding expectation. The object must
    contain the exact same keys as the expectation, no more, no less.
    """

    @classmethod
    def matches(cls, expectation: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided expectation can be handled by this asserter.

        This asserter can handle any mapping expectation.

        :param expectation: expectation to be tested
        :return: whether expectation can be handled by this asserter
        """
        return isinstance(expectation, Mapping)

    def __init__(
        self,
        asserter_factory: type[AsserterFactoryProtocol],
        expectation: Mapping[Any, Any],
    ) -> None:
        super().__init__(asserter_factory, expectation)
        self._items_asserters = {
            key: asserter_factory.create(expectation) for key, expectation in expectation.items()
        }

    def assert_object(self, object_: Any) -> None:  # noqa: ANN401
        """
        Assert if the expectation is fulfilled by an object.

        :param object_: an object to be tested
        """
        assert isinstance(object_, Mapping), f'Object must be a mapping. Got: {type(object_)}.'
        assert object_.keys() == self._items_asserters.keys(), (
            'Object keys must be equal to expectation keys.'
        )
        for key, asserter in self._items_asserters.items():
            object_value = object_[key]
            try:
                asserter.assert_object(object_value)
            except AssertionError as exc:
                msg = f'Mapping value for key "{key}" is invalid. {exc!s}'
                raise AssertionError(msg) from None
