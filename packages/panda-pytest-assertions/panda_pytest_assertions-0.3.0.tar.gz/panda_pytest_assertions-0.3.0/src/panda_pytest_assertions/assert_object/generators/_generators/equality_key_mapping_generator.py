from collections.abc import Mapping
from typing import Any

from panda_pytest_assertions.assert_object import GeneratorFactoryProtocol

from .exceptions import ObjectNotMatchingDefinitionError
from .generator import Generator


class EqualityKeyMappingGenerator(Generator):
    """
    Generates Mapping expectation using keys' values as keys' expectations.
    """

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definiton can be handled by this generator.

        This generator can handle any Mapping as definition.

        :param definition: definition to be tested
        :return: whether definition can be handled by this generator
        """
        return isinstance(definition, Mapping)

    def __init__(
        self,
        generator_factory: type[GeneratorFactoryProtocol],
        definition: Mapping[Any, Any],
    ) -> None:
        super().__init__(generator_factory, definition)
        self.items_generators = {key: generator_factory.create(value) for key, value in definition.items()}

    def generate_expectation(self, object_: Any) -> Mapping[Any, Any]:  # noqa: ANN401
        """
        Generate expectation from given object.

        :param object_: an object to generate expectation from
        :return: generated expectation
        """
        if not isinstance(object_, Mapping):
            msg = f'Expected mapping, got {type(object_)}'
            raise ObjectNotMatchingDefinitionError(msg)
        if object_.keys() != self.items_generators.keys():
            msg = (
                f'Object has invalid keys. '
                f'Expected: {set(self.items_generators.keys())}, got {set(object_.keys())}.'
            )
            raise ObjectNotMatchingDefinitionError(msg)
        return {
            key: value_generator.generate_expectation(object_[key])
            for key, value_generator in self.items_generators.items()
        }
