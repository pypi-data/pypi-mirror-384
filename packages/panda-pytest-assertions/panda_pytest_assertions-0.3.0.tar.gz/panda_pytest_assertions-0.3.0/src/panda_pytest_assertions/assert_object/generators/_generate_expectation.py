from typing import Any

from panda_pytest_assertions.assert_object._protocols import GeneratorFactoryProtocol

from ._generator_factories import BuiltInGeneratorFactory


def generate_expectation(
    object_: Any,  # noqa: ANN401
    definition: Any,  # noqa: ANN401
    *,
    generator_factory: type[GeneratorFactoryProtocol] = BuiltInGeneratorFactory,
) -> Any:  # noqa: ANN401
    """
    Generate expectation for given object according to definition.

    :param object_: object to generate expectation from
    :param definition: expectation definition
    :param generator_factory: factory used to create generators
    :return: generated expectation
    """
    generator = generator_factory.create(definition)
    return generator.generate_expectation(object_)
