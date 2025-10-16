class Stringified:
    """
    Wrapper for the expectation that describes stringified object.
    """

    def __init__(self, stringified_value: str, /) -> None:
        #: stringified value expectation
        self.stringified_value = stringified_value

    def __repr__(self) -> str:
        return f'Stringified({self.stringified_value!r})'
