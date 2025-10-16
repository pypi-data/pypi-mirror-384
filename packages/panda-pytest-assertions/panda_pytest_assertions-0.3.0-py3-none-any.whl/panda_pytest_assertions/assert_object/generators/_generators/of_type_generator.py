from types import NoneType
from typing import Any

from panda_pytest_assertions.assert_object import GeneratorFactoryProtocol

from .._expectation_definitions import OfTypeDef  # noqa: TID252
from .exceptions import ObjectNotMatchingDefinitionError
from .generator import Generator


class OfTypeGenerator(Generator):
    """
    Generates custom expectation, but only if the object is of a correct type.
    """

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definiton can be handled by this generator.

        This generator can handle OfTypeDef definition.

        :param definition: definition to be tested
        :return: whether definition can be handled by this generator
        """
        return isinstance(definition, OfTypeDef)

    def __init__(
        self,
        generator_factory: type[GeneratorFactoryProtocol],
        definition: OfTypeDef,
    ) -> None:
        super().__init__(generator_factory, definition)
        self.object_generator = generator_factory.create(definition.object_definition)
        self.expected_type = definition.expected_type if definition.expected_type is not None else NoneType

    def generate_expectation(self, object_: Any) -> Any:  # noqa: ANN401
        """
        Generate expectation from given object.

        :param object_: an object to generate expectation from
        :return: generated expectation
        """
        if not isinstance(object_, self.expected_type):
            msg = f'Object is expected to be "{self.expected_type}" type. Got "{type(object_)}".'
            raise ObjectNotMatchingDefinitionError(msg)
        return self.object_generator.generate_expectation(object_)
