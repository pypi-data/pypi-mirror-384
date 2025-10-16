from unittest.mock import MagicMock

from panda_pytest_assertions.assert_object import MappingSubset


def test_init():
    expectations = MagicMock()
    assert MappingSubset(expectations).items_expectations is expectations


def test_repr():
    expectations = MagicMock()
    assert repr(MappingSubset(expectations)) == f'MappingSubset({expectations!r})'
