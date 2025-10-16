from collections.abc import Callable
from typing import Any

import pytest
from _pytest.outcomes import Failed

from panda_pytest_assertions.assert_context import assert_context, AssertContext, ExceptionMatch


def do_nothing(_: AssertContext) -> None:
    pass


def raise_system_exit(_: AssertContext) -> None:
    msg = 'yes'
    raise SystemExit(msg)


def set_123(context: AssertContext) -> None:
    context.set(123)


def set_none(context: AssertContext) -> None:
    context.set(None)


def set_123_and_raise_system_exit(context: AssertContext) -> None:
    context.set(123)
    msg = 'yes'
    raise SystemExit(msg)


@pytest.mark.parametrize(
    ['function', 'arguments', 'expected_exception'],
    [
        (do_nothing, {}, None),
        (do_nothing, {'exception': SystemExit}, Failed),
        (do_nothing, {'exception': ValueError}, Failed),
        (do_nothing, {'exception': None}, None),
        (do_nothing, {'exception': ExceptionMatch(SystemExit, 'yes')}, Failed),
        (do_nothing, {'exception': ExceptionMatch(SystemExit, 'no')}, Failed),
        (do_nothing, {'exception': ExceptionMatch(ValueError, 'yes')}, Failed),
        (do_nothing, {'result': 123}, AssertionError),
        (do_nothing, {'result': None}, AssertionError),
        (do_nothing, {'exception': SystemExit, 'result': 123}, Failed),
        (do_nothing, {'exception': ValueError, 'result': 123}, Failed),
        (do_nothing, {'exception': None, 'result': 123}, AssertionError),
        (do_nothing, {'behaviour': SystemExit}, Failed),
        (do_nothing, {'behaviour': ValueError}, Failed),
        (do_nothing, {'behaviour': ExceptionMatch(SystemExit, 'yes')}, Failed),
        (do_nothing, {'behaviour': ExceptionMatch(SystemExit, 'no')}, Failed),
        (do_nothing, {'behaviour': ExceptionMatch(ValueError, 'yes')}, Failed),
        (do_nothing, {'behaviour': 123}, AssertionError),
        (do_nothing, {'behaviour': None}, AssertionError),
        (raise_system_exit, {}, SystemExit),
        (raise_system_exit, {'exception': SystemExit}, None),
        (raise_system_exit, {'exception': ValueError}, SystemExit),
        (raise_system_exit, {'exception': None}, SystemExit),
        (raise_system_exit, {'exception': ExceptionMatch(SystemExit, 'yes')}, None),
        (raise_system_exit, {'exception': ExceptionMatch(SystemExit, 'no')}, AssertionError),
        (raise_system_exit, {'exception': ExceptionMatch(ValueError, 'yes')}, SystemExit),
        (raise_system_exit, {'result': 123}, SystemExit),
        (raise_system_exit, {'result': None}, SystemExit),
        (raise_system_exit, {'exception': SystemExit, 'result': 123}, AssertionError),
        (raise_system_exit, {'exception': ValueError, 'result': 123}, SystemExit),
        (raise_system_exit, {'exception': None, 'result': 123}, SystemExit),
        (raise_system_exit, {'behaviour': SystemExit}, None),
        (raise_system_exit, {'behaviour': ValueError}, SystemExit),
        (raise_system_exit, {'behaviour': ExceptionMatch(SystemExit, 'yes')}, None),
        (raise_system_exit, {'behaviour': ExceptionMatch(SystemExit, 'no')}, AssertionError),
        (raise_system_exit, {'behaviour': ExceptionMatch(ValueError, 'yes')}, SystemExit),
        (raise_system_exit, {'behaviour': 123}, SystemExit),
        (raise_system_exit, {'behaviour': None}, SystemExit),
        (set_123, {}, AssertionError),
        (set_123, {'exception': SystemExit}, Failed),
        (set_123, {'exception': ValueError}, Failed),
        (set_123, {'exception': None}, AssertionError),
        (set_123, {'exception': ExceptionMatch(SystemExit, 'yes')}, Failed),
        (set_123, {'exception': ExceptionMatch(SystemExit, 'no')}, Failed),
        (set_123, {'exception': ExceptionMatch(ValueError, 'yes')}, Failed),
        (set_123, {'result': 123}, None),
        (set_123, {'result': None}, AssertionError),
        (set_123, {'exception': SystemExit, 'result': 123}, Failed),
        (set_123, {'exception': ValueError, 'result': 123}, Failed),
        (set_123, {'exception': None, 'result': 123}, None),
        (set_123, {'behaviour': SystemExit}, Failed),
        (set_123, {'behaviour': ValueError}, Failed),
        (set_123, {'behaviour': ExceptionMatch(SystemExit, 'yes')}, Failed),
        (set_123, {'behaviour': ExceptionMatch(SystemExit, 'no')}, Failed),
        (set_123, {'behaviour': ExceptionMatch(ValueError, 'yes')}, Failed),
        (set_123, {'behaviour': 123}, None),
        (set_123, {'behaviour': None}, AssertionError),
        (set_none, {}, AssertionError),
        (set_none, {'exception': SystemExit}, Failed),
        (set_none, {'exception': ValueError}, Failed),
        (set_none, {'exception': None}, AssertionError),
        (set_none, {'exception': ExceptionMatch(SystemExit, 'yes')}, Failed),
        (set_none, {'exception': ExceptionMatch(SystemExit, 'no')}, Failed),
        (set_none, {'exception': ExceptionMatch(ValueError, 'yes')}, Failed),
        (set_none, {'result': 123}, AssertionError),
        (set_none, {'result': None}, None),
        (set_none, {'exception': SystemExit, 'result': 123}, Failed),
        (set_none, {'exception': ValueError, 'result': 123}, Failed),
        (set_none, {'exception': None, 'result': 123}, AssertionError),
        (set_none, {'behaviour': SystemExit}, Failed),
        (set_none, {'behaviour': ValueError}, Failed),
        (set_none, {'behaviour': ExceptionMatch(SystemExit, 'yes')}, Failed),
        (set_none, {'behaviour': ExceptionMatch(SystemExit, 'no')}, Failed),
        (set_none, {'behaviour': ExceptionMatch(ValueError, 'yes')}, Failed),
        (set_none, {'behaviour': 123}, AssertionError),
        (set_none, {'behaviour': None}, None),
        (set_123_and_raise_system_exit, {}, SystemExit),
        (set_123_and_raise_system_exit, {'exception': SystemExit}, AssertionError),
        (set_123_and_raise_system_exit, {'exception': ValueError}, SystemExit),
        (set_123_and_raise_system_exit, {'exception': None}, SystemExit),
        (set_123_and_raise_system_exit, {'exception': ExceptionMatch(SystemExit, 'yes')}, AssertionError),
        (set_123_and_raise_system_exit, {'exception': ExceptionMatch(SystemExit, 'no')}, AssertionError),
        (set_123_and_raise_system_exit, {'exception': ExceptionMatch(ValueError, 'yes')}, SystemExit),
        (set_123_and_raise_system_exit, {'result': 123}, SystemExit),
        (set_123_and_raise_system_exit, {'result': None}, SystemExit),
        (set_123_and_raise_system_exit, {'exception': SystemExit, 'result': 123}, None),
        (set_123_and_raise_system_exit, {'exception': ValueError, 'result': 123}, SystemExit),
        (set_123_and_raise_system_exit, {'exception': None, 'result': 123}, SystemExit),
        (set_123_and_raise_system_exit, {'behaviour': SystemExit}, AssertionError),
        (set_123_and_raise_system_exit, {'behaviour': ValueError}, SystemExit),
        (set_123_and_raise_system_exit, {'behaviour': ExceptionMatch(SystemExit, 'yes')}, AssertionError),
        (set_123_and_raise_system_exit, {'behaviour': ExceptionMatch(SystemExit, 'no')}, AssertionError),
        (set_123_and_raise_system_exit, {'behaviour': ExceptionMatch(ValueError, 'yes')}, SystemExit),
        (set_123_and_raise_system_exit, {'behaviour': 123}, SystemExit),
        (set_123_and_raise_system_exit, {'behaviour': None}, SystemExit),
    ],
)
def test(
    function: Callable[[AssertContext], None],
    arguments: dict[str, Any],
    expected_exception: type[Exception] | None,
):
    try:
        with assert_context(**arguments) as context:
            function(context)
    except BaseException as exc:  # noqa: BLE001
        assert expected_exception is not None, (  # noqa: PT017
            f'Block is not expected to raise {type(exc)} for args: {arguments}'
        )
        assert type(exc) is expected_exception, (  # noqa: PT017
            f'Block is expected to raise {expected_exception} not {type(exc)}'
        )
    else:
        assert expected_exception is None, (
            f'Block is expected to raise {type(expected_exception)} for args: {arguments}'
        )


def test_parameters_exclusiveness():
    with pytest.raises(AssertionError):
        assert_context(  # type: ignore [call-overload]
            behaviour=None,
            result=None,
        ).__enter__()

    with pytest.raises(AssertionError):
        assert_context(  # type: ignore [call-overload]
            behaviour=None,
            exception=None,
        ).__enter__()

    with pytest.raises(AssertionError):
        assert_context(  # type: ignore [call-overload]
            behaviour=None,
            result=None,
            exception=None,
        ).__enter__()
