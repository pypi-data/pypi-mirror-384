from unittest.mock import MagicMock

from panda_pytest_assertions.assert_object.generators import ObjectAttributesDef


def test_init():
    attributes_definitions = MagicMock()

    instance = ObjectAttributesDef(attributes_definitions)

    assert instance.attributes_definitions is attributes_definitions
