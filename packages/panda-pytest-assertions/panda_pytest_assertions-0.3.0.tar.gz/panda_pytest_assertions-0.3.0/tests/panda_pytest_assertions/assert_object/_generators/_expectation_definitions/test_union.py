from unittest.mock import MagicMock

from panda_pytest_assertions.assert_object.generators import UnionDef


def test_init():
    definition_1 = MagicMock()
    definition_2 = MagicMock()
    definition_3 = MagicMock()

    instance = UnionDef(definition_1, definition_2, definition_3)

    assert instance.definitions == (definition_1, definition_2, definition_3)
