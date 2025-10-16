from collections.abc import Iterable
from typing import Any

from panda_pytest_assertions.assert_object import GeneratorFactoryProtocol

from .._expectation_definitions import UniformOrderedDef  # noqa: TID252
from .exceptions import ObjectNotMatchingDefinitionError
from .generator import Generator


class UniformOrderedGenerator(Generator):
    """
    Generates ordered collection expectation using the same definition for each element.
    """

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definiton can be handled by this generator.

        This generator can handle OrderedDef definition.

        :param definition: definition to be tested
        :return: whether definition can be handled by this generator
        """
        return isinstance(definition, UniformOrderedDef)

    def __init__(
        self,
        generator_factory: type[GeneratorFactoryProtocol],
        definition: UniformOrderedDef,
    ) -> None:
        super().__init__(generator_factory, definition)
        self.elements_generator = generator_factory.create(definition.elements_definition)
        self.expectation_type = definition.expectation_type

    def generate_expectation(self, object_: Any) -> list[Any] | tuple[Any, ...]:  # noqa: ANN401
        """
        Generate expectation from given object.

        :param object_: an object to generate expectation from
        :return: generated expectation
        """
        if not isinstance(object_, Iterable):
            msg = f'Expected iterale, got {type(object_)}'
            raise ObjectNotMatchingDefinitionError(msg)
        return self.expectation_type(
            self.elements_generator.generate_expectation(element) for element in object_
        )
