from typing import Any

from panda_pytest_assertions.assert_object._protocols import AsserterFactoryProtocol

from .._expectation_modificators import Stringified  # noqa: TID252
from .asserter import Asserter


class StringifiedAsserter(Asserter):
    """
    Assert that the stringified object is a given value.
    """

    @classmethod
    def matches(cls, expectation: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided expectation can be handled by this asserter.

        This asserter can handle a Stringified expectation.

        :param expectation: expectation to be tested
        :return: whether expectation can be handled by this asserter
        """
        return isinstance(expectation, Stringified)

    def __init__(self, asserter_factory: type[AsserterFactoryProtocol], expectation: Stringified) -> None:
        super().__init__(asserter_factory, expectation)
        self.expected_value = expectation.stringified_value

    def assert_object(self, object_: Any) -> None:  # noqa: ANN401
        """
        Assert if the expectation is fulfilled by an object.

        :param object_: an object to be tested
        """
        assert str(object_) == self.expected_value, 'Stringified value of an object is invalid.'
