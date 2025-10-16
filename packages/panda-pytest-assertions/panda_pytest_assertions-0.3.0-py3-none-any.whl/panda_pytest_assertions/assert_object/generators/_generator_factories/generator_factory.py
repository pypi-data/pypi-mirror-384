from collections import deque
from typing import Any, ClassVar

from panda_pytest_assertions.assert_object._protocols import GeneratorProtocol


class GeneratorFactory:
    """
    Factory for registered generators.
    """

    #: list of registered gnerator classes
    _GENERATOR_TYPES: ClassVar[deque[type[GeneratorProtocol]]] = deque()

    @classmethod
    def create(cls, definition: Any) -> Any:  # noqa: ANN401
        """
        Create expectation generator for given definition.

        The method goes through all registered generator types and uses the first one that matches.

        :param definition: expectation definition
        :return: generated expectation
        """
        for generator_type in cls._GENERATOR_TYPES:
            if generator_type.matches(definition):
                return generator_type(cls, definition)
        msg = (
            f'None of the registered generators matches definition "{definition}" '
            f'of type "{type(definition)}".'
        )
        raise ValueError(msg)

    @classmethod
    def register_generator(
        cls,
        generator: type[GeneratorProtocol],
        *,
        after: type[GeneratorProtocol] | None = None,
        before: type[GeneratorProtocol] | None = None,
    ) -> None:
        """
        Register the provided generator to be used.

        The generator is registered at the earliest possible position. If `after` and `before`
        parameters are not set, it is registered at the beginning of the list to be matched
        when creating generator for expectations.

        :param generator: generator to be registered
        :param after: registered generator must be matched after this one
        :param before: registered generator must be matched before this one
        """
        if '_GENERATOR_TYPES' not in cls.__dict__:
            cls._GENERATOR_TYPES = cls._GENERATOR_TYPES.copy()

        after_position = cls._GENERATOR_TYPES.index(after) if after is not None else -1
        before_position = (
            cls._GENERATOR_TYPES.index(before) if before is not None else len(cls._GENERATOR_TYPES) + 1
        )
        if after_position >= before_position:
            msg = (
                f'Cannot register generator between "{after}" and "{before}" as their '
                f'respective positions are: "{after_position}" and "{before_position}"'
            )
            raise ValueError(msg)
        cls._GENERATOR_TYPES.insert(after_position + 1, generator)
