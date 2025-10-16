from collections.abc import Mapping
from typing import Any

from panda_pytest_assertions.assert_object import GeneratorFactoryProtocol

from .._expectation_definitions import UniformMappingDef  # noqa: TID252
from .exceptions import ObjectNotMatchingDefinitionError
from .generator import Generator


class UniformMappingGenerator(Generator):
    """
    Generates mapping expectation using the same definition for each value.
    """

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definiton can be handled by this generator.

        This generator can handle UniformMappingDef definition.

        :param definition: definition to be tested
        :return: whether definition can be handled by this generator
        """
        return isinstance(definition, UniformMappingDef)

    def __init__(
        self,
        generator_factory: type[GeneratorFactoryProtocol],
        definition: UniformMappingDef,
    ) -> None:
        super().__init__(generator_factory, definition)
        self.keys_generator = generator_factory.create(definition.keys_definition)
        self.values_generator = generator_factory.create(definition.values_definition)

    def generate_expectation(self, object_: Any) -> Mapping[Any, Any]:  # noqa: ANN401
        """
        Generate expectation from given object.

        :param object_: an object to generate expectation from
        :return: generated expectation
        """
        if not isinstance(object_, Mapping):
            msg = f'Expected mapping, got {type(object_)}'
            raise ObjectNotMatchingDefinitionError(msg)
        return {
            self.keys_generator.generate_expectation(key): self.values_generator.generate_expectation(value)
            for key, value in object_.items()
        }
