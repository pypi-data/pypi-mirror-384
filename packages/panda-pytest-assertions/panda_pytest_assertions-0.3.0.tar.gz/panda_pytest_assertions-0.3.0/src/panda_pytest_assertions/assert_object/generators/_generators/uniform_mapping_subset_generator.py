from collections.abc import Mapping
from typing import Any

from panda_pytest_assertions.assert_object import GeneratorFactoryProtocol, MappingSubset

from .._expectation_definitions import UniformMappingSubsetDef  # noqa: TID252
from .exceptions import ObjectNotMatchingDefinitionError
from .generator import Generator


class UniformMappingSubsetGenerator(Generator):
    """
    Generates MappingSubset expectation using the same definition for each value.
    """

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definiton can be handled by this generator.

        This generator can handle UniformMappingSubsetDef definition.

        :param definition: definition to be tested
        :return: whether definition can be handled by this generator
        """
        return isinstance(definition, UniformMappingSubsetDef)

    def __init__(
        self,
        generator_factory: type[GeneratorFactoryProtocol],
        definition: UniformMappingSubsetDef,
    ) -> None:
        super().__init__(generator_factory, definition)
        self.keys_generator = generator_factory.create(definition.keys_definition)
        self.values_generator = generator_factory.create(definition.values_definition)

    def generate_expectation(self, object_: Any) -> MappingSubset:  # noqa: ANN401
        """
        Generate expectation from given object.

        :param object_: an object to generate expectation from
        :return: generated expectation
        """
        if not isinstance(object_, Mapping):
            msg = f'Expected mapping, got {type(object_)}'
            raise ObjectNotMatchingDefinitionError(msg)
        items_expectations = {}
        for key, value in object_.items():
            key_expectation = self.keys_generator.generate_expectation(key)
            value_expectation = self.values_generator.generate_expectation(value)
            items_expectations[key_expectation] = value_expectation
        return MappingSubset(items_expectations)
