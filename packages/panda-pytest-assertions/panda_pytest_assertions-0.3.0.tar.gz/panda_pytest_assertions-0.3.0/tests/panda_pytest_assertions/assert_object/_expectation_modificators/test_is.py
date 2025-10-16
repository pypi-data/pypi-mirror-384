from unittest.mock import MagicMock

from panda_pytest_assertions.assert_object import Is


def test_init():
    value = MagicMock()

    instance = Is(value)

    assert instance.value is value


def test_repr():
    value = MagicMock()

    instance = Is(value)

    assert repr(instance) == f'Is({value!r})'
