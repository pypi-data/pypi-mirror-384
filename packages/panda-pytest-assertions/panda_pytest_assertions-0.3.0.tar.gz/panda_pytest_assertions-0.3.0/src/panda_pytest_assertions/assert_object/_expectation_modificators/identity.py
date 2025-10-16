from typing import Any


class Is:
    """
    Wrapper for the expectation that describes object identity (compared with `is` operator).
    """

    def __init__(self, value: Any, /) -> None:  # noqa: ANN401
        #: expected object
        self.value = value

    def __repr__(self) -> str:
        return f'Is({self.value!r})'
