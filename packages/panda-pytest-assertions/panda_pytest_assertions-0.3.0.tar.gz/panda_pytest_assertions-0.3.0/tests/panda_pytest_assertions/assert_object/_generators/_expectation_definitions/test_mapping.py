from unittest.mock import MagicMock

from panda_pytest_assertions.assert_object.generators import MappingDef


def test_init():
    keys_definition = MagicMock()
    items_definitions = MagicMock()

    instance = MappingDef(keys_definition, items_definitions)

    assert instance.keys_definition is keys_definition
    assert instance.items_definitions is items_definitions
