from panda_pytest_assertions.assert_object._objects_asserters import (
    EqualityAsserter,
    IdentityAsserter,
    IsTypeAsserter,
    MappingAsserter,
    MappingSubsetAsserter,
    ObjectAttributesAsserter,
    OrderedElementsAsserter,
    StringifiedAsserter,
    UnorderedElementsAsserter,
    WithTypeAsserter,
)

from .asserter_factory import AsserterFactory


class BuiltInAsserterFactory(AsserterFactory):
    """
    Factory that has all built-in asserters registered.
    """


# MUST be the first one as it implements a fallback mechanism and matches everything
BuiltInAsserterFactory.register_asserter(EqualityAsserter)
BuiltInAsserterFactory.register_asserter(IdentityAsserter)
BuiltInAsserterFactory.register_asserter(IsTypeAsserter)
BuiltInAsserterFactory.register_asserter(MappingAsserter)
BuiltInAsserterFactory.register_asserter(MappingSubsetAsserter)
BuiltInAsserterFactory.register_asserter(ObjectAttributesAsserter)
BuiltInAsserterFactory.register_asserter(OrderedElementsAsserter)
BuiltInAsserterFactory.register_asserter(StringifiedAsserter)
BuiltInAsserterFactory.register_asserter(UnorderedElementsAsserter)
BuiltInAsserterFactory.register_asserter(WithTypeAsserter)
