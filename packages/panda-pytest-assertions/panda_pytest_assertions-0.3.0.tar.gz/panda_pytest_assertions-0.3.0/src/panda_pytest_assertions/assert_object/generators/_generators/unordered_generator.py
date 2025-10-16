from collections.abc import Iterable
from typing import Any

from panda_pytest_assertions.assert_object import GeneratorFactoryProtocol, Unordered

from .._expectation_definitions import UniformUnorderedDef  # noqa: TID252
from .exceptions import ObjectNotMatchingDefinitionError
from .generator import Generator


class UnorderedGenerator(Generator):
    """
    Generates unordered collection expectation.
    """

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definiton can be handled by this generator.

        This generator can handle UniformUnorderedDef definition.

        :param definition: definition to be tested
        :return: whether definition can be handled by this generator
        """
        return isinstance(definition, UniformUnorderedDef)

    def __init__(
        self,
        generator_factory: type[GeneratorFactoryProtocol],
        definition: UniformUnorderedDef,
    ) -> None:
        super().__init__(generator_factory, definition)
        self.elements_generator = generator_factory.create(definition.elements_definition)

    def generate_expectation(self, object_: Any) -> Unordered:  # noqa: ANN401
        """
        Generate expectation from given object.

        :param object_: an object to generate expectation from
        :return: generated expectation
        """
        if not isinstance(object_, Iterable):
            msg = f'Expected iterale, got {type(object_)}'
            raise ObjectNotMatchingDefinitionError(msg)
        return Unordered([self.elements_generator.generate_expectation(element) for element in object_])
