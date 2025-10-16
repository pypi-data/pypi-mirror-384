import abc
from typing import Any

from panda_pytest_assertions.assert_object._protocols import AsserterFactoryProtocol


class Asserter(abc.ABC):
    """
    Asserter checking that the given expectation is fulfilled by the object.
    """

    @classmethod
    @abc.abstractmethod
    def matches(cls, expectation: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided expectation can be handled by this asserter.

        :param expectation: expectation to be tested
        """

    def __init__(
        self,
        asserter_factory: type[AsserterFactoryProtocol],
        expectation: Any,  # noqa: ANN401
    ) -> None:
        self.asserter_factory = asserter_factory
        self.expectation = expectation

    @abc.abstractmethod
    def assert_object(self, object_: Any) -> None:  # noqa: ANN401
        """
        Assert if the expectation is fulfilled by an object.

        :param object_: an object to be tested
        """
