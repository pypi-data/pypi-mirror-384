from typing import Any

from panda_pytest_assertions.assert_object._protocols import AsserterFactoryProtocol

from .._expectation_modificators import Is  # noqa: TID252
from .asserter import Asserter


class IdentityAsserter(Asserter):
    """
    Assert that the object is identical to the expectation's value.
    """

    @classmethod
    def matches(cls, expectation: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided expectation can be handled by this asserter.

        This asserter can handle an Is expectation.

        :param expectation: expectation to be tested
        :return: whether expectation can be handled by this asserter
        """
        return isinstance(expectation, Is)

    def __init__(self, asserter_factory: type[AsserterFactoryProtocol], expectation: Is) -> None:
        super().__init__(asserter_factory, expectation)
        self.expected_object = expectation.value

    def assert_object(self, object_: Any) -> None:  # noqa: ANN401
        """
        Assert if the expectation is fulfilled by an object.

        :param object_: an object to be tested
        """
        assert self.expected_object is object_
