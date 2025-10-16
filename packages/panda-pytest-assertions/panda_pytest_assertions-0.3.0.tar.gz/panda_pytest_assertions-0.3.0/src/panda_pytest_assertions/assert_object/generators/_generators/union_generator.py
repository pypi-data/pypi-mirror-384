from typing import Any

from panda_pytest_assertions.assert_object import GeneratorFactoryProtocol

from .._expectation_definitions import UnionDef  # noqa: TID252
from .exceptions import ObjectNotMatchingDefinitionError
from .generator import Generator


class UnionGenerator(Generator):
    """
    Generates expectation using the first definition that matches the value.
    """

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definiton can be handled by this generator.

        This generator can handle UniformMappingDef definition.

        :param definition: definition to be tested
        :return: whether definition can be handled by this generator
        """
        return isinstance(definition, UnionDef)

    def __init__(
        self,
        generator_factory: type[GeneratorFactoryProtocol],
        definition: UnionDef,
    ) -> None:
        super().__init__(generator_factory, definition)
        self.generators = tuple(
            generator_factory.create(single_definition) for single_definition in definition.definitions
        )

    def generate_expectation(self, object_: Any) -> Any:  # noqa: ANN401
        """
        Generate expectation from given object.

        :param object_: an object to generate expectation from
        :return: generated expectation
        """
        exceptions = []
        for generator in self.generators:
            try:
                return generator.generate_expectation(object_)
            except ObjectNotMatchingDefinitionError as exc:  # noqa: PERF203
                exceptions.append(exc)
        msg = f'Object "{object_}" did not match any of the expectation definition. Errors: {exceptions!r}'
        raise ObjectNotMatchingDefinitionError(msg)
