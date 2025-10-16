from typing import Any

from panda_pytest_assertions.assert_object import GeneratorFactoryProtocol, WithType

from .._expectation_definitions import WithTypeDef  # noqa: TID252
from .generator import Generator


class WithTypeGenerator(Generator):
    """
    Generates WithType expectation.
    """

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definiton can be handled by this generator.

        This generator can handle WithTypeDef definition.

        :param definition: definition to be tested
        :return: whether definition can be handled by this generator
        """
        return isinstance(definition, WithTypeDef)

    def __init__(
        self,
        generator_factory: type[GeneratorFactoryProtocol],
        definition: WithTypeDef,
    ) -> None:
        super().__init__(generator_factory, definition)
        self.object_generator = generator_factory.create(definition.object_definition)
        self.include_module = definition.include_module

    def generate_expectation(self, object_: Any) -> WithType:  # noqa: ANN401
        """
        Generate expectation from given object.

        :param object_: an object to generate expectation from
        :return: generated expectation
        """
        return WithType(
            self.object_generator.generate_expectation(object_),
            object_.__class__.__name__,
            object_.__class__.__module__ if self.include_module else None,
        )
