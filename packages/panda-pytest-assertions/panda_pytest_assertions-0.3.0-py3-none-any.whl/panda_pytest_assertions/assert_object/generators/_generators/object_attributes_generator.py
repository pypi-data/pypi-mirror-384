from typing import Any

from panda_pytest_assertions.assert_object import GeneratorFactoryProtocol, ObjectAttributes

from .._expectation_definitions import ObjectAttributesDef  # noqa: TID252
from .exceptions import ObjectNotMatchingDefinitionError
from .generator import Generator


class ObjectAttributesGenerator(Generator):
    """
    Generates ObjectAttributes expectation.
    """

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definiton can be handled by this generator.

        This generator can handle ObjectAttributesDef definition.

        :param definition: definition to be tested
        :return: whether definition can be handled by this generator
        """
        return isinstance(definition, ObjectAttributesDef)

    def __init__(
        self,
        generator_factory: type[GeneratorFactoryProtocol],
        definition: ObjectAttributesDef,
    ) -> None:
        super().__init__(generator_factory, definition)
        self.attributes_generators = {
            attr_name: generator_factory.create(attr_definition)
            for attr_name, attr_definition in definition.attributes_definitions.items()
        }

    def generate_expectation(self, object_: Any) -> ObjectAttributes:  # noqa: ANN401
        """
        Generate expectation from given object.

        :param object_: an object to generate expectation from
        :return: generated expectation
        """
        attributes_expectations = {}
        for attr_name, attr_generator in self.attributes_generators.items():
            if not hasattr(object_, attr_name):
                msg = f'"{object_}" does not have an attribute names "{attr_name}"'
                raise ObjectNotMatchingDefinitionError(msg)
            attributes_expectations[attr_name] = attr_generator.generate_expectation(
                getattr(object_, attr_name),
            )
        return ObjectAttributes(attributes_expectations)
