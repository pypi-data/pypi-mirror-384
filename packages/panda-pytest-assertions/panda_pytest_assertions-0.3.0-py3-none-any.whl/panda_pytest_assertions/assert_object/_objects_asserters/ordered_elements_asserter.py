from collections.abc import Iterable, Sequence
from typing import Any

from panda_pytest_assertions.assert_object._protocols import AsserterFactoryProtocol

from .asserter import Asserter


class OrderedElementsAsserter(Asserter):
    """
    Assert that elements of a flat collection are fulfill by provided expectations.

    The order of expectations must match the order fo elements.
    """

    @classmethod
    def matches(cls, expectation: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided expectation can be handled by this asserter.

        This asserter can handle a list or a tuple expectation.

        :param expectation: expectation to be tested
        :return: whether expectation can be handled by this asserter
        """
        return isinstance(expectation, list | tuple)

    def __init__(
        self,
        asserter_factory: type[AsserterFactoryProtocol],
        expectation: list[Any] | tuple[Any, ...],
    ) -> None:
        super().__init__(asserter_factory, expectation)
        self._elements_asserters = [
            asserter_factory.create(element_expectation) for element_expectation in expectation
        ]

    def assert_object(self, object_: Sequence[Any]) -> None:
        """
        Assert if the expectation is fulfilled by an object.

        :param object_: an object to be tested
        """
        assert isinstance(object_, Iterable), f'Object must be iterable. Got: {type(object_)}.'
        elements = list(object_)
        assert len(elements) == len(self._elements_asserters), (
            f'Length of an object ({len(elements)}) does not equal to the number of '
            f'expectations ({len(self._elements_asserters)}).'
        )
        for index, (element, asserter) in enumerate(zip(elements, self._elements_asserters, strict=True)):
            try:
                asserter.assert_object(element)
            except AssertionError as exc:  # noqa: PERF203
                msg = f'Element with index [{index}] has invalid value. {exc!s}'
                raise AssertionError(msg) from None
