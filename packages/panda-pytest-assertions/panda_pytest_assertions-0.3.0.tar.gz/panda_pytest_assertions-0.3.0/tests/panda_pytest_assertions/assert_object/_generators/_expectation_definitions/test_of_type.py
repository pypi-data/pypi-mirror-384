from unittest.mock import MagicMock

from panda_pytest_assertions.assert_object.generators import OfTypeDef


def test_init():
    expected_type = MagicMock()
    object_definition = MagicMock()

    instance = OfTypeDef(expected_type, object_definition)

    assert instance.expected_type is expected_type
    assert instance.object_definition is object_definition
