from inspect import isabstract

from panda_pytest_assertions.assert_object import _objects_asserters, BuiltInAsserterFactory


def test_built_in_asserter_factory_registered():
    for built_in_asserter in filter(
        lambda value: isinstance(value, type) and not isabstract(value),
        _objects_asserters.__dict__.values(),
    ):
        assert built_in_asserter in BuiltInAsserterFactory._ASSERTER_TYPES
