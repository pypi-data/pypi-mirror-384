from unittest.mock import MagicMock

from panda_pytest_assertions.assert_object import Unordered


def test_init():
    expectations = MagicMock()
    assert Unordered(expectations).elements_expectations is expectations


def test_iter():
    expectations = [1, 2, 3, 4, 5]
    assert list(Unordered(expectations)) == expectations


def test_repr():
    expectations = MagicMock()
    assert repr(Unordered(expectations)) == f'Unordered({expectations!r})'
