from unittest.mock import MagicMock

from panda_pytest_assertions.assert_object import Stringified


def test_init():
    expectations = MagicMock()
    assert Stringified(expectations).stringified_value is expectations


def test_repr():
    expectations = MagicMock()
    assert repr(Stringified(expectations)) == f'Stringified({expectations!r})'
