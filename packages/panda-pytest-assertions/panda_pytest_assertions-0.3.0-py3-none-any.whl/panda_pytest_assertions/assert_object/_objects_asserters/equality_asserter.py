from typing import Any

from .asserter import Asserter


class EqualityAsserter(Asserter):
    """
    Assert that the object is equal to the expectation.

    It is a default, fallback asserter that matches ANY object, so it is critical that it is
    the last one checked.
    """

    @classmethod
    def matches(cls, expectation: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided expectation can be handled by this asserter.

        This asserter can handle any object, as __eq__ is defined for all types.

        :param expectation: expectation to be tested
        :return: whether expectation can be handled by this asserter
        """
        _ = expectation
        return True

    def assert_object(self, object_: Any) -> None:  # noqa: ANN401
        """
        Assert if the expectation is fulfilled by an object.

        :param object_: an object to be tested
        """
        assert self.expectation == object_
