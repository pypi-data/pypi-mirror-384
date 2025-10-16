from unittest.mock import MagicMock

from panda_pytest_assertions.assert_object.generators import IsTypeDef


def test_init():
    include_module = MagicMock()

    instance = IsTypeDef(include_module=include_module)

    assert instance.include_module is include_module
