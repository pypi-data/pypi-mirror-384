from collections import deque
from typing import Any, ClassVar

from panda_pytest_assertions.assert_object._protocols import AsserterProtocol


class AsserterFactory:
    """
    Factory for registered asserters.
    """

    #: list of registered asserter classes
    _ASSERTER_TYPES: ClassVar[deque[type[AsserterProtocol]]] = deque()

    @classmethod
    def create(cls, expectation: Any) -> AsserterProtocol:  # noqa: ANN401
        """
        Create asserter object for given expectation.

        The function goes through all registered asserter types and creates the first one that matches.

        :param expectation: expectation to create asserter for
        :return: created asserter
        """
        for asserter_type in cls._ASSERTER_TYPES:
            if asserter_type.matches(expectation):
                return asserter_type(cls, expectation)
        msg = (
            f'None of the registered asserters matches expectation "{expectation}" '
            f'of type "{type(expectation)}".'
        )
        raise ValueError(msg)

    @classmethod
    def register_asserter(
        cls,
        asserter: type[AsserterProtocol],
        *,
        after: type[AsserterProtocol] | None = None,
        before: type[AsserterProtocol] | None = None,
    ) -> None:
        """
        Register the provided asserter to be used.

        The asserter is registered at the earliest possible position. If `after` and `before`
        parameters are not set, it is registered at the beginning of the list to be matched
        when creating asserter for expectations.

        :param asserter: asserter to be registered
        :param after: registered asserter must be matched after this one
        :param before: registered asserter must be matched before this one
        """
        if '_ASSERTER_TYPES' not in cls.__dict__:
            cls._ASSERTER_TYPES = cls._ASSERTER_TYPES.copy()

        after_position = cls._ASSERTER_TYPES.index(after) if after is not None else -1
        before_position = (
            cls._ASSERTER_TYPES.index(before) if before is not None else len(cls._ASSERTER_TYPES) + 1
        )
        if after_position >= before_position:
            msg = (
                f'Cannot register asserter between "{after}" and "{before}" as their '
                f'respective positions are: "{after_position}" and "{before_position}"'
            )
            raise ValueError(msg)
        cls._ASSERTER_TYPES.insert(after_position + 1, asserter)
