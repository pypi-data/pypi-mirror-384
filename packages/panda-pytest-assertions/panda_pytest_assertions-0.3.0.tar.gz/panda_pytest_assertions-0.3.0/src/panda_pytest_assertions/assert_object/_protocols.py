from typing import Any, Protocol


class AsserterProtocol(Protocol):
    """
    Asserter checking that the given expectation is fulfilled by the object.
    """

    expectation: Any
    asserter_factory: 'type[AsserterFactoryProtocol]'

    def __init__(
        self,
        asserter_factory: 'type[AsserterFactoryProtocol]',
        expectation: Any,  # noqa: ANN401
    ) -> None: ...

    @classmethod
    def matches(cls, expectation: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided expectation can be handled by this asserter.

        :param expectation: expectation to be tested
        """

    def assert_object(self, object_: Any) -> None:  # noqa: ANN401
        """
        Assert if the expectation is fulfilled by an object.

        :param object_: an object to be tested
        """


class AsserterFactoryProtocol(Protocol):
    """
    Factory for registered asserters.
    """

    @classmethod
    def create(cls, expectation: Any) -> AsserterProtocol:  # noqa: ANN401
        """
        Create asserter object for given expectation.

        The function goes through all registered asserter types and creates the first one that matches.

        :param expectation: expectation to create asserter for
        """


class GeneratorProtocol(Protocol):
    """
    Generates expectation from given object according to a definition.
    """

    definition: Any
    generator_factory: 'type[GeneratorFactoryProtocol]'

    def __init__(
        self,
        generator_factory: 'type[GeneratorFactoryProtocol]',
        definition: Any,  # noqa: ANN401
    ) -> None: ...

    @classmethod
    def matches(cls, definition: Any) -> bool:  # noqa: ANN401
        """
        Decide whether provided definition can be handled by this generator.

        :param definition: definition to be tested
        """

    def generate_expectation(self, object_: Any) -> Any:  # noqa: ANN401
        """
        Generate expectation from given object.

        :param object_: an object to generate expectation from
        """


class GeneratorFactoryProtocol(Protocol):
    """
    Factory for registered generators.
    """

    @classmethod
    def create(cls, definition: Any) -> GeneratorProtocol:  # noqa: ANN401
        """
        Create expectation generator for given definition.

        The method goes through all registered generator types and uses the first one that matches.

        :param definition: expectation definition
        """
