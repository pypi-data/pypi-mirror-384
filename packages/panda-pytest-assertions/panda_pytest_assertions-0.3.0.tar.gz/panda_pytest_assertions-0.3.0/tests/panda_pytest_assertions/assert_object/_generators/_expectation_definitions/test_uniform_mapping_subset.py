from unittest.mock import MagicMock

from panda_pytest_assertions.assert_object.generators import UniformMappingSubsetDef


def test_init():
    keys_definition = MagicMock()
    values_definition = MagicMock()

    instance = UniformMappingSubsetDef(keys_definition, values_definition)

    assert instance.keys_definition is keys_definition
    assert instance.values_definition == values_definition
