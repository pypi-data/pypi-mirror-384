from typing import Any

from panda_pytest_assertions.assert_object import Stringified

from .._expectation_definitions import StringifiedDef  # noqa: TID252
from .generator import Generator


class StringifiedGenerator(Generator):
    """
    Generates Stringified expectation from the object.
    """

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definiton can be handled by this generator.

        This generator can handle StringifiedDef definition.

        :param definition: definition to be tested
        :return: whether definition can be handled by this generator
        """
        return isinstance(definition, StringifiedDef) or (
            isinstance(definition, type) and issubclass(definition, StringifiedDef)
        )

    def generate_expectation(self, object_: Any) -> Any:  # noqa: ANN401
        """
        Generate Stringified expectation from given object.

        :param object_: an object to generate expectation from
        :return: generated expectation
        """
        return Stringified(str(object_))
