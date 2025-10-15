import os
import contextvars
import inspect
from contextlib import contextmanager
from enum import Enum
from functools import wraps
from pprint import pformat
from typing import (
    Any,
    Callable,
    ContextManager,
    Literal,
    overload,
    TypedDict,
)

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)
from opentelemetry.trace import Span as OTelSpan

from vals.sdk.auth import be_host, _get_auth_token
from vals.sdk.exceptions import IncorrectSpanTypeError, SpanNotFoundError

__all__ = [
    "get_current_span",
    "Span",
    "LLMSpan",
    "Trace",
    "get_client",
    "SpanType",
    "SpanLevel",
    "Usage",
]


def _get_func_args(func: Callable, args: tuple, kwargs: dict) -> dict[str, Any]:
    """Inspect a function and its arguments and return a dictionary of arguments, excluding 'self'."""
    try:
        bound_args = inspect.signature(func).bind(*args, **kwargs)
        bound_args.apply_defaults()
        arguments = bound_args.arguments
        if "self" in arguments:
            del arguments["self"]
        return arguments
    except (TypeError, ValueError):
        # Fallback for functions that can't be inspected.
        # Heuristic to remove self from args if it looks like a method call.
        if args and hasattr(args[0], func.__name__):
            return {"args": args[1:], "kwargs": kwargs}
        return {"args": args, "kwargs": kwargs}


_current_span: contextvars.ContextVar["Span | LLMSpan | None"] = contextvars.ContextVar(
    "current_custom_span", default=None
)


class Usage(TypedDict, total=False):
    in_tokens: int
    out_tokens: int
    reasoning_tokens: int


class SpanType(Enum):
    LOGIC = "logic"
    LLM = "llm"
    TOOL = "tool"


class SpanLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    DEBUG = "debug"
    ERROR = "error"


def _serialize_and_set_attributes(otel_span: OTelSpan, attributes: dict[str, Any]):
    """Serializes dictionary values to JSON and sets them as span attributes."""
    for name, value in attributes.items():
        if value is not None:
            otel_span.set_attribute(name, pformat(value))


class Span:
    """Represents a single operation within a trace.

    Spans are created via a `Trace` object's `.span()` decorator or
    `.start_as_current_span()` context manager.

    Attributes:
        span_type: The type of the span (e.g., logic, llm, tool).
    """

    def __init__(
        self,
        otel_span: OTelSpan,
        span_type: SpanType = SpanType.LOGIC,
    ):
        self.span_type = span_type
        self._otel_span = otel_span
        self._otel_span.set_attribute("span_type", span_type.value)

    def update(
        self,
        *,
        input: Any = None,
        output: Any = None,
        metadata: Any = None,
        level: SpanLevel | None = None,
        status_message: str | None = None,
    ):
        """Updates the span with new attributes.

        Args:
            input: The input data for the operation (JSON serializable).
            output: The output data from the operation (JSON serializable).
            metadata: Additional metadata (JSON serializable).
            level: The severity level of the span (e.g., INFO, WARNING, ERROR).
            status_message: A message describing the status of the operation.
        """
        if level:
            self._otel_span.set_attribute("level", level.value)
        if status_message:
            self._otel_span.set_attribute("status_message", status_message)

        attributes_to_serialize = {
            "input": input,
            "output": output,
            "metadata": metadata,
        }
        _serialize_and_set_attributes(self._otel_span, attributes_to_serialize)


class LLMSpan(Span):
    """A specialized Span for tracing Large Language Model (LLM) operations."""

    def __init__(self, otel_span: OTelSpan):
        super().__init__(otel_span, span_type=SpanType.LLM)

    def update(
        self,
        *,
        model: str | None = None,
        input: Any = None,
        output: Any = None,
        reasoning: Any = None,
        usage: Usage | None = None,
        metadata: Any = None,
        level: SpanLevel | None = None,
        status_message: str | None = None,
    ):
        """Updates the LLM span with new attributes.

        Extends the base `Span.update` to include LLM-specific attributes.

        Args:
            model: The name of the language model used.
            input: The input to the operation (e.g., prompt).
            output: The output from the operation (e.g., model response).
            reasoning: The model's reasoning process, if available.
            usage: A `Usage` object containing token counts.
            metadata: Additional metadata.
            level: The severity level of the span.
            status_message: A message describing the status.
        """
        super().update(
            input=input,
            output=output,
            metadata=metadata,
            level=level,
            status_message=status_message,
        )

        if model:
            self._otel_span.set_attribute("model", model)

        if usage:
            if "in_tokens" in usage and usage["in_tokens"] is not None:
                self._otel_span.set_attribute("usage.in_tokens", usage["in_tokens"])
            if "out_tokens" in usage and usage["out_tokens"] is not None:
                self._otel_span.set_attribute("usage.out_tokens", usage["out_tokens"])
            if "reasoning_tokens" in usage and usage["reasoning_tokens"] is not None:
                self._otel_span.set_attribute(
                    "usage.reasoning_tokens", usage["reasoning_tokens"]
                )

        attributes_to_serialize = {
            "reasoning": reasoning,
        }
        _serialize_and_set_attributes(self._otel_span, attributes_to_serialize)


class Trace:
    """Manages the creation and processing of spans for a tracing session.

    This class is the main entry point for the tracing SDK, providing methods
    to create spans via decorators (`.span()`) or context managers
    (`.start_as_current_span()`).

    Args:
        name: The name of the tracer (e.g., the instrumented module's name).
        project_slug: The project slug for sending traces. Defaults to "default-project".
    """

    def __init__(self, name: str, project_slug: str = "default-project"):
        otlp_exporter = OTLPSpanExporter(
            endpoint=f"{be_host()}/upload_otel_spans/{project_slug}/",
            headers={"Authorization": _get_auth_token()},
        )
        processor = BatchSpanProcessor(otlp_exporter)

        self.provider = TracerProvider()
        self.provider.add_span_processor(processor)

        trace.set_tracer_provider(self.provider)

        self._tracer = trace.get_tracer(name)

    @overload
    def start_as_current_span(
        self, name: str, *, span_type: Literal[SpanType.LLM]
    ) -> ContextManager[LLMSpan]: ...

    @overload
    def start_as_current_span(
        self,
        name: str,
        *,
        span_type: Literal[SpanType.LOGIC, SpanType.TOOL] = SpanType.LOGIC,
    ) -> ContextManager[Span]: ...

    @contextmanager
    def start_as_current_span(self, name: str, *, span_type: SpanType = SpanType.LOGIC):
        """Starts a new span as a context manager.

        Args:
            name: The name of the span representing the operation.
            span_type: The type of span. Use `SpanType.LLM` for LLM operations.
                Defaults to `SpanType.LOGIC`.

        Yields:
            The newly created `Span` or `LLMSpan` object.

        Usage:
            with trace.start_as_current_span("my_operation") as span:
                ...
        """
        with self._tracer.start_as_current_span(name) as otel_span:
            if span_type == SpanType.LLM:
                span = LLMSpan(otel_span=otel_span)
            else:
                span = Span(otel_span=otel_span, span_type=span_type)

            token = _current_span.set(span)
            try:
                yield span
            except Exception as e:
                span.update(
                    level=SpanLevel.ERROR,
                    status_message=str(e),
                )
                raise
            finally:
                _current_span.reset(token)

    def span(
        self,
        func: Callable | None = None,
        *,
        name: str | None = None,
        span_type: SpanType = SpanType.LOGIC,
    ) -> Callable:
        """Decorator to wrap a function execution in a new span.

        Automatically records function arguments as span input and return value as output.

        Usage:
            @trace.span
            @trace.span(name="custom_name")

        Args:
            func: The function to be decorated (handled automatically).
            name: Optional name for the span. Defaults to the function's name.
            span_type: The type of span. Defaults to `SpanType.LOGIC`.

        Returns:
            The decorated function.
        """

        def decorator(func: Callable):
            span_name = name or func.__name__

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.start_as_current_span(span_name, span_type=span_type) as span:
                    func_args = _get_func_args(func, args, kwargs)
                    span.update(input=func_args)
                    result = await func(*args, **kwargs)
                    span.update(output=result)
                    return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.start_as_current_span(span_name, span_type=span_type) as span:
                    func_args = _get_func_args(func, args, kwargs)
                    span.update(input=func_args)
                    result = func(*args, **kwargs)
                    span.update(output=result)
                    return result

            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        if func is None:
            return decorator
        else:
            return decorator(func)


def get_client(name: str = "", project_slug: str = "default-project") -> Trace:
    """Gets a `Trace` client, inferring the name from the calling module.

    Args:
        name: The name for the tracer. If empty, inferred from the caller's filename.
        project_slug: The project slug for sending traces. Defaults to "default-project".

    Returns:
        A `Trace` instance.
    """
    if not name:
        caller_frame = inspect.stack()[1]
        caller_file_path = caller_frame.filename
        filename_without_ext = os.path.splitext(os.path.basename(caller_file_path))[0]
        name = filename_without_ext
    return Trace(name, project_slug=project_slug)


@overload
def get_current_span(span_type: Literal[SpanType.LLM]) -> "LLMSpan": ...


@overload
def get_current_span(span_type: Literal[SpanType.LOGIC, SpanType.TOOL]) -> "Span": ...


@overload
def get_current_span() -> "Span": ...


def get_current_span(
    span_type: SpanType | None = None,
) -> "Span | LLMSpan":
    """Retrieves the currently active Span from the context.

    Args:
        span_type: The expected type of the span. If provided, the function will
            ensure the current span is of this type.

    Raises:
        SpanNotFoundError: If called outside of an active span context.
        IncorrectSpanTypeError: If the active span is not of the expected type.

    Returns:
        The currently active Span or LLMSpan object.
    """
    span = _current_span.get()
    if not span:
        raise SpanNotFoundError()

    if span_type == SpanType.LLM and not isinstance(span, LLMSpan):
        raise IncorrectSpanTypeError(
            f"Expected span of type {span_type.value}, but got {span.span_type.value}"
        )

    return span
