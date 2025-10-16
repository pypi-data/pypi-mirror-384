from unittest.mock import MagicMock

from panda_pytest_assertions.assert_object.generators import UniformUnorderedDef


def test_init():
    elements_definition = MagicMock()

    instance = UniformUnorderedDef(elements_definition)

    assert instance.elements_definition is elements_definition
