from collections.abc import Generator
from contextlib import contextmanager, ExitStack, nullcontext
from typing import Any, NamedTuple, overload

import pytest


class _Unset:
    __instance: '_Unset | None' = None

    def __new__(cls) -> '_Unset':
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance


_UNSET = _Unset()


class AssertContext:
    __slots__ = ('_result',)

    def __init__(self) -> None:
        self._result: Any = _UNSET

    def set(self, value: Any) -> None:  # noqa: ANN401
        self._result = value

    @contextmanager
    def assert_result_equal(self, expected_result: Any) -> Generator[None, None, None]:  # noqa: ANN401
        yield
        assert expected_result == self._result


class ExceptionMatch(NamedTuple):
    #: type of expected exception
    type_: type[BaseException]
    #: match parameter passed to pytest.raises
    match_: str


@overload
@contextmanager
def assert_context(  # noqa: D418
    *,
    exception: type[BaseException] | ExceptionMatch | None | _Unset = ...,
    result: Any | _Unset = ...,  # noqa: ANN401
) -> Generator[AssertContext, None, None]:
    """
    Context manager that makes sure `with` block behaved according to the arguments.

    If the `exception` parameter is set to exception type, the `with` block is expected to raise an exception
    of provided type. If the `exception` parameter is set to an instance of `ExceptionMatch` class, the `with`
    block is expected to raise an exception of type specified in `type_` field and the value that matches the
    string specified in `match_` field. For exact matching logic see `match` parameter of the `pytest.raises`.
    If the `exception` parameter is NOT set or is set to `None`, the `with` block is expected NOT TO raise
    any exceptions.

    If the `result` parameter is set, its value is expected to be equal to `with` block result. The `with`
    block result is set with the `set` method of an object yielded by the context manager. The comparison
    is used with `==` operator, where `result` argument is on the left side.
    If the `result` parameter is NOT set, the `set` method of yielded object is expected
    not to be called at all.

    :param exception: specification of exception, expected to be raised
    :param result: value expected to be set with `set` method of yielded object
    """


@overload
@contextmanager
def assert_context(  # noqa: D418
    *,
    behaviour: type[BaseException] | ExceptionMatch | Any | _Unset = ...,  # noqa: ANN401
) -> Generator[AssertContext, None, None]:
    """
    Context manager that makes sure `with` block behaved according to the arguments.

    Context manager yields a single object used that provides `set` method used to set the `with`
    block result that is to be asserted.

    If the `behaviour` parameter is set to exception type, the `with` block is expected to raise an exception
    of provided type. If the `behaviour` parameter is set to an instance of `ExceptionMatch` class, the `with`
    block is expected to raise an exception of type specified in `type_` field and the value that matches the
    string specified in `match_` field. For exact matching logic see `match` parameter of the `pytest.raises`.
    In both cases the `set` method of yielded object is expected not to be called at all.

    If the `behaviour` parameter is set to anything else, its value is expected to be equal to `with`
    block result. The comparison is used with `==` operator, where `result` argument is on the left side and
    the `with` block is expected to not raise any exceptions.

    If the `behaviour` parameter is NOT set, the `with` block is expected NOT TO raise any exceptions and
    the `set` method of yielded object is expected not to be called at all.

    :param behaviour: describes expected behaviour of the `with` block
    """


@contextmanager
def assert_context(
    *,
    exception: type[BaseException] | ExceptionMatch | None | _Unset = _UNSET,
    result: Any | _Unset = _UNSET,
    behaviour: type[BaseException] | ExceptionMatch | Any | _Unset = _UNSET,
) -> Generator[AssertContext, None, None]:
    """
    Context manager that makes sure `with` block behaved according to the arguments.

    Pair of parameters `exception` and `result` are exclusive with parameter `behaviour`. If `behaviour`
    is set to an exception type or `ExceptionMatch` instance, it is the same as if `exception` would be set to
    this value and `result` would not be set. If `behaviour` is set to any other value, its treated as the
    value of `result` and the `exception` remains unset.

    If the `exception` parameter is set to exception type, the `with` block is expected to raise an exception
    of provided type. If the `exception` parameter is set to an instance of `ExceptionMatch` class, the `with`
    block is expected to raise an exception of type specified in `type_` field and the value that matches the
    string specified in `match_` field. For exact matching logic see `match` parameter of the `pytest.raises`.
    If the `exception` parameter is NOT set or is set to `None`, the `with` block is expected NOT TO raise
    any exceptions.

    If the `result` parameter is set, its value is expected to be equal to `with` block result. The `with`
    block result is set with the `set` method of an object yielded by the context manager. The comparison
    is used with `==` operator, where `result` argument is on the left side.
    If the `result` parameter is NOT set, the `set` method of yielded object is expected
    not to be called at all.

    :param exception: specification of exception, expected to be raised
    :param result: value expected to be set with `set` method of yielded object
    :param behaviour: a common name for `exception` and `result` parameters, exclusive to them
    :yield: object used to set the result of a `with` block
    """
    if behaviour != _UNSET:
        assert exception == _UNSET
        assert result == _UNSET
        if isinstance(behaviour, ExceptionMatch) or (
            isinstance(behaviour, type) and issubclass(behaviour, BaseException)
        ):
            exception = behaviour
        else:
            result = behaviour
    if isinstance(exception, ExceptionMatch):
        match_ = exception.match_
        exception = exception.type_
    else:
        match_ = None
    context = AssertContext()
    exception_behaviour = (
        nullcontext()
        if isinstance(exception, _Unset | None)
        else pytest.raises(
            exception,
            match=match_,
        )
    )

    with ExitStack() as behaviours_stack:
        behaviours_stack.enter_context(context.assert_result_equal(result))
        behaviours_stack.enter_context(exception_behaviour)
        yield context
