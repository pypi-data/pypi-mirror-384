from collections.abc import Iterable
from typing import Any

from panda_pytest_assertions.assert_object import GeneratorFactoryProtocol

from .exceptions import ObjectNotMatchingDefinitionError
from .generator import Generator


class OrderedGenerator(Generator):
    """
    Generates ordered collection expectation.
    """

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definiton can be handled by this generator.

        This generator can handle any list or tuple definition.

        :param definition: definition to be tested
        :return: whether definition can be handled by this generator
        """
        return isinstance(definition, list | tuple)

    def __init__(
        self,
        generator_factory: type[GeneratorFactoryProtocol],
        definition: list[Any] | tuple[Any, ...],
    ) -> None:
        super().__init__(generator_factory, definition)
        self.elements_generators = [generator_factory.create(element) for element in definition]
        self.expectation_type = type(definition)

    def generate_expectation(self, object_: Any) -> list[Any] | tuple[Any, ...]:  # noqa: ANN401
        """
        Generate expectation from given object.

        :param object_: an object to generate expectation from
        :return: generated expectation
        """
        if not isinstance(object_, Iterable):
            msg = f'Expected iterale, got {type(object_)}'
            raise ObjectNotMatchingDefinitionError(msg)
        elements = list(object_)
        if len(elements) != len(self.elements_generators):
            msg = (
                f'Object has incorrect lenght. Expected {len(self.elements_generators)}, got {len(elements)}.'
            )
            raise ObjectNotMatchingDefinitionError(msg)
        return self.expectation_type(
            generator.generate_expectation(element)
            for element, generator in zip(elements, self.elements_generators, strict=True)
        )
