from collections.abc import Mapping
from typing import Any

from panda_pytest_assertions.assert_object import GeneratorFactoryProtocol, MappingSubset

from .._expectation_definitions import MappingSubsetDef  # noqa: TID252
from .exceptions import ObjectNotMatchingDefinitionError
from .generator import Generator


class MappingSubsetGenerator(Generator):
    """
    Generates MappingSubset expectation.
    """

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definiton can be handled by this generator.

        This generator can handle MappingSubsetDef definition.

        :param definition: definition to be tested
        :return: whether definition can be handled by this generator
        """
        return isinstance(definition, MappingSubsetDef)

    def __init__(
        self,
        generator_factory: type[GeneratorFactoryProtocol],
        definition: MappingSubsetDef,
    ) -> None:
        super().__init__(generator_factory, definition)
        self.keys_generator = generator_factory.create(definition.keys_definition)
        self.items_generators = {
            key: generator_factory.create(value) for key, value in definition.items_definitions.items()
        }

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
        for key, value_generator in self.items_generators.items():
            if key not in object_:
                msg = f'"{object_}" does not contain a key "{key}"'
                raise ObjectNotMatchingDefinitionError(msg)
            key_expectation = self.keys_generator.generate_expectation(key)
            value_expectation = value_generator.generate_expectation(object_[key])
            items_expectations[key_expectation] = value_expectation
        return MappingSubset(items_expectations)
