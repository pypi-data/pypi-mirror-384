class ValsException(Exception):
    """
    An exception returned when there is an error querying the Vals SDK.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class SpanNotFoundError(ValsException):
    """Raised when a span is expected but not found in the current context."""

    def __init__(self, message: str = "No active span context found."):
        super().__init__(message)


class IncorrectSpanTypeError(ValsException):
    """Raised when a span is of an unexpected type (e.g., expecting LLMSpan)."""

    def __init__(self, message: str = "The current span is not of the expected type."):
        super().__init__(message)
