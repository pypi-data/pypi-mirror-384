from unittest.mock import MagicMock

from panda_pytest_assertions.assert_object import ObjectAttributes


def test_init():
    expectations = MagicMock()
    assert ObjectAttributes(expectations).attributes_expectations is expectations


def test_repr():
    expectations = MagicMock()
    assert repr(ObjectAttributes(expectations)) == f'ObjectAttributes({expectations!r})'
