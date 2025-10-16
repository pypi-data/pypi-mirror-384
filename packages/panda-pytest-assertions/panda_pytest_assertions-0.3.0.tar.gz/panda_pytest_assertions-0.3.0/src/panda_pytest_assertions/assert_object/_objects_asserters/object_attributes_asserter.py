from typing import Any

from panda_pytest_assertions.assert_object._protocols import AsserterFactoryProtocol

from .._expectation_modificators import ObjectAttributes  # noqa: TID252
from .asserter import Asserter


class ObjectAttributesAsserter(Asserter):
    """
    Assert the values of object's attributes fulfill expectation defined in the dictionary.

    Expectation dictionary is a mapping between attribute name and its expectation.
    """

    @classmethod
    def matches(cls, expectation: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided expectation can be handled by this asserter.

        This asserter can handle an ObjectAttributes expectation.

        :param expectation: expectation to be tested
        :return: whether expectation can be handled by this asserter
        """
        return isinstance(expectation, ObjectAttributes)

    def __init__(
        self,
        asserter_factory: type[AsserterFactoryProtocol],
        expectation: ObjectAttributes,
    ) -> None:
        super().__init__(asserter_factory, expectation)
        self._attributes_asserters = {
            attr_name: asserter_factory.create(attr_expectation)
            for attr_name, attr_expectation in expectation.attributes_expectations.items()
        }

    def assert_object(self, object_: Any) -> None:  # noqa: ANN401
        """
        Assert if the expectation is fulfilled by an object.

        :param object_: an object to be tested
        """
        for attr_name, attr_asserter in self._attributes_asserters.items():
            assert hasattr(object_, attr_name), f'Objects is missing attribute "{attr_name}".'
            attr_value = getattr(object_, attr_name)
            try:
                attr_asserter.assert_object(attr_value)
            except AssertionError as exc:
                msg = f'Objects attribute "{attr_name}" has invalid value. {exc!s}'
                raise AssertionError(msg) from None
