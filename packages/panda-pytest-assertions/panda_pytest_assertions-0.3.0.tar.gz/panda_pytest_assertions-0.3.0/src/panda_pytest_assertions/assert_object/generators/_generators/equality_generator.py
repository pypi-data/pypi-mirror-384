from typing import Any

from .._expectation_definitions import EqualityDef  # noqa: TID252
from .generator import Generator


class EqualityGenerator(Generator):
    """
    Generated expectation is just the specific object.
    """

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definiton can be handled by this generator.

        This generator can handle EqualityDef definition.

        :param definition: definition to be tested
        :return: whether definition can be handled by this generator
        """
        return isinstance(definition, EqualityDef) or (
            isinstance(definition, type) and issubclass(definition, EqualityDef)
        )

    def generate_expectation(self, object_: Any) -> Any:  # noqa: ANN401
        """
        Generate expectation from given object.

        Return object itself.

        :param object_: an object to generate expectation from
        :return: generated expectation
        """
        return object_
