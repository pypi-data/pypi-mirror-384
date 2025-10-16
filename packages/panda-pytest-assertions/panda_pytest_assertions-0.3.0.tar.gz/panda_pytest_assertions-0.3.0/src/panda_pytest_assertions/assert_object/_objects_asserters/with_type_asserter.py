from typing import Any

from panda_pytest_assertions.assert_object._protocols import AsserterFactoryProtocol

from .._expectation_modificators import WithType  # noqa: TID252
from .asserter import Asserter


class WithTypeAsserter(Asserter):
    """
    Assert that the object matches given expectation and is of a proper type.
    """

    @classmethod
    def matches(cls, expectation: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided expectation can be handled by this asserter.

        This asserter can handle a WithType expectation.

        :param expectation: expectation to be tested
        :return: whether expectation can be handled by this asserter
        """
        return isinstance(expectation, WithType)

    def __init__(self, asserter_factory: type[AsserterFactoryProtocol], expectation: WithType) -> None:
        super().__init__(asserter_factory, expectation)
        self.expected_type_name = expectation.expected_type_name
        self.expected_type_module = expectation.expected_type_module
        self.object_asserter = asserter_factory.create(expectation.expectation)

    def assert_object(self, object_: Any) -> None:  # noqa: ANN401
        """
        Assert if the expectation is fulfilled by an object.

        :param object_: an object to be tested
        """
        if object_.__class__.__name__ != self.expected_type_name:
            msg = (
                f'Object type ("{type(object_)}") has invalid name. '
                f'Expected "{self.expected_type_name}", got "{object_.__class__.__name__}".'
            )
            raise AssertionError(msg)
        if (
            self.expected_type_module is not None
            and object_.__class__.__module__ != self.expected_type_module
        ):
            msg = (
                f'Object type ("{type(object_)}") is from invalid module. '
                f'Expected "{self.expected_type_module}", got "{object_.__class__.__module__}".'
            )
            raise AssertionError(msg)
        try:
            self.object_asserter.assert_object(object_)
        except AssertionError as exc:
            msg = f'Object is invalid. {exc!s}'
            raise AssertionError(msg) from None
