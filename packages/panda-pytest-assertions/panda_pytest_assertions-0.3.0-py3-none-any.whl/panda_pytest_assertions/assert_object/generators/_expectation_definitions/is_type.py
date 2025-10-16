class IsTypeDef:
    """
    Defines expectation validating object type.
    """

    def __init__(self, /, *, include_module: bool = True) -> None:
        #: indicator whether module shall be included in IsType expectation
        self.include_module = include_module
