from typing import Any
from unittest.mock import MagicMock

import pytest

from panda_pytest_assertions.assert_object.generators import uniform_ordered_def, UniformOrderedDef


def test_init():
    elements_definition = MagicMock()
    expectation_type = MagicMock()

    instance = UniformOrderedDef(elements_definition, expectation_type=expectation_type)

    assert instance.elements_definition is elements_definition
    assert instance.expectation_type is expectation_type


@pytest.mark.parametrize('expectation_type', [list, tuple])
def test_ordered_def(expectation_type: type[list[Any]] | type[tuple[Any, ...]]):
    elements_definition = MagicMock()

    instance = uniform_ordered_def(expectation_type=expectation_type)(elements_definition)

    assert instance.elements_definition is elements_definition
    assert instance.expectation_type is expectation_type
