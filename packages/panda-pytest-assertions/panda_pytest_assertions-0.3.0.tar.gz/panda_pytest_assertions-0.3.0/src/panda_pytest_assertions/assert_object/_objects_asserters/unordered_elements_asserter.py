from collections.abc import Iterable
from typing import Any

from panda_pytest_assertions.assert_object._protocols import AsserterFactoryProtocol, AsserterProtocol

from .._expectation_modificators import Unordered  # noqa: TID252
from .asserter import Asserter


class UnorderedElementsAsserter(Asserter):
    """
    Assert that elements of a flat collection are fulfill by provided expectations.

    The order of expectations does not matter, but all elements of an array must match at least one
    expectation and each expectation must match at least one element.

    The algorithm iterates over expectatations and if any of the element matches an expectation,
    both expectation and element are not considered anymore.
    """

    @classmethod
    def matches(cls, expectation: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided expectation can be handled by this asserter.

        This asserter can handle an UnorderedList or a set expectation.

        :param expectation: expectation to be tested
        :return: whether expectation can be handled by this asserter
        """
        return isinstance(expectation, Unordered | set)

    def __init__(
        self,
        asserter_factory: type[AsserterFactoryProtocol],
        expectation: Unordered | set[Any],
    ) -> None:
        super().__init__(asserter_factory, expectation)
        self._elements_asserters = [
            asserter_factory.create(element_expectation) for element_expectation in expectation
        ]

    def assert_object(self, object_: Iterable[Any]) -> None:
        """
        Assert if the expectation is fulfilled by an object.

        :param object_: an object to be tested
        """
        assert isinstance(object_, Iterable), f'Object must be iterable. Got: {type(object_)}.'
        elements_yet_not_fulfilled = list(object_)
        assert len(elements_yet_not_fulfilled) == len(self._elements_asserters), (
            f'Length of an object ({len(elements_yet_not_fulfilled)}) does not equal to the number of '
            f'expectations ({len(self._elements_asserters)})'
        )
        for element_asserter in self._elements_asserters:
            matching_element = self._get_first_element_asserting(element_asserter, elements_yet_not_fulfilled)
            if matching_element is not None:
                elements_yet_not_fulfilled.remove(matching_element)
                continue
            msg = (
                f'None of the elements of a collection has fulfilled expectation '
                f'"{element_asserter.expectation!r}"'
            )
            raise AssertionError(msg)

    @staticmethod
    def _get_first_element_asserting(
        element_asserter: AsserterProtocol,
        elements: list[Any],
    ) -> Any | None:  # noqa: ANN401
        for element in elements:
            try:
                element_asserter.assert_object(element)
            except Exception:  # noqa: S112, BLE001
                continue
            return element
        return None
