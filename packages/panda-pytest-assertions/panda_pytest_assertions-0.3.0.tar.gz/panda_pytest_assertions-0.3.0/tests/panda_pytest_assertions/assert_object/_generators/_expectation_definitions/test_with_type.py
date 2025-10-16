from unittest.mock import MagicMock

import pytest

from panda_pytest_assertions.assert_object.generators import with_type_def, WithTypeDef


def test_init():
    object_definition = MagicMock()
    include_module = MagicMock()

    instance = WithTypeDef(object_definition, include_module=include_module)

    assert instance.object_definition is object_definition
    assert instance.include_module is include_module


@pytest.mark.parametrize('include_module', [True, False])
def test_with_type_def(include_module: bool):
    object_definition = MagicMock()

    instance = with_type_def(include_module=include_module)(object_definition)

    assert instance.object_definition is object_definition
    assert instance.include_module is include_module
