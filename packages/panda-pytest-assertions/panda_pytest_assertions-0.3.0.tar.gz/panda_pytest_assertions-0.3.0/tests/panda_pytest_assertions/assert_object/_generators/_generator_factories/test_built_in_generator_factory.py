from inspect import isabstract

from panda_pytest_assertions.assert_object.generators import _generators, BuiltInGeneratorFactory


def test_built_in_asserter_factory_registered():
    for built_in_asserter in filter(
        lambda value: isinstance(value, type) and not isabstract(value),
        _generators.__dict__.values(),
    ):
        assert built_in_asserter in BuiltInGeneratorFactory._GENERATOR_TYPES
