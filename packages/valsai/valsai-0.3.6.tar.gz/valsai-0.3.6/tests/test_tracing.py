import asyncio
import unittest
from unittest.mock import MagicMock, patch

from vals.sdk.tracing import (
    LLMSpan,
    Span,
    SpanType,
    Trace,
    get_current_span,
)


class TestTracing(unittest.TestCase):
    def setUp(self):
        """Set up a mock tracer for all tests."""
        self.mock_otel_span = MagicMock()
        self.mock_tracer = MagicMock()
        self.mock_tracer.start_as_current_span.return_value.__enter__.return_value = (
            self.mock_otel_span
        )

        patcher_exporter = patch("vals.sdk.tracing.OTLPSpanExporter", spec=True)
        patcher_processor = patch("vals.sdk.tracing.BatchSpanProcessor", spec=True)
        patcher_trace = patch("vals.sdk.tracing.trace.get_tracer")
        patcher_auth = patch("vals.sdk.tracing._get_auth_token")

        self.addCleanup(patcher_exporter.stop)
        self.addCleanup(patcher_processor.stop)
        self.addCleanup(patcher_trace.stop)
        self.addCleanup(patcher_auth.stop)

        self.mock_get_tracer = patcher_trace.start()
        patcher_processor.start()
        patcher_exporter.start()
        mock_auth = patcher_auth.start()
        mock_auth.return_value = "test-token"

        self.mock_get_tracer.return_value = self.mock_tracer
        self.trace = Trace("test_tracer")

    def test_decorator_does_not_interfere(self):
        """Ensure a decorated function's logic runs and returns correctly."""

        @self.trace.span()
        def sample_function(x, y):
            return x + y

        self.assertEqual(sample_function(2, 3), 5)

    def test_context_manager_does_not_interfere(self):
        """Ensure code inside a 'with' block executes."""
        executed = False
        with self.trace.start_as_current_span("test_span"):
            executed = True
        self.assertTrue(executed)

    def test_exception_propagation_decorator(self):
        """Ensure exceptions from decorated functions are propagated."""

        @self.trace.span()
        def failing_function():
            raise ValueError("Test error")

        with self.assertRaises(ValueError):
            failing_function()

    def test_exception_propagation_context_manager(self):
        """Ensure exceptions from 'with' blocks are propagated."""
        with self.assertRaises(ValueError):
            with self.trace.start_as_current_span("test_span"):
                raise ValueError("Test error")
        # Check that error information was set on the span
        self.mock_otel_span.set_attribute.assert_any_call("level", "error")
        self.mock_otel_span.set_attribute.assert_any_call(
            "status_message", "Test error"
        )

    def test_sync_decorator(self):
        """Test the decorator on a synchronous function."""

        @self.trace.span()
        def sync_func():
            return "sync_result"

        self.assertEqual(sync_func(), "sync_result")
        self.mock_tracer.start_as_current_span.assert_called_with("sync_func")

    def test_async_decorator(self):
        """Test the decorator on an asynchronous function."""

        @self.trace.span
        async def async_func():
            await asyncio.sleep(0.01)
            return "async_result"

        result = asyncio.run(async_func())
        self.assertEqual(result, "async_result")
        self.mock_tracer.start_as_current_span.assert_called_with("async_func")

    def test_nested_decorators(self):
        """Test nested decorated functions to ensure context is handled."""

        @self.trace.span(name="inner")
        def inner_func():
            # When this is called, the current span should be 'inner'
            self.assertEqual(get_current_span()._otel_span, self.mock_otel_span)
            return "inner_result"

        @self.trace.span(name="outer")
        def outer_func():
            # The current span is 'outer' here
            self.assertEqual(get_current_span()._otel_span, self.mock_otel_span)
            return inner_func()

        self.assertEqual(outer_func(), "inner_result")

    def test_nested_context_managers(self):
        """Test nested 'with' blocks."""
        with self.trace.start_as_current_span("outer_span") as outer_span:
            self.assertEqual(get_current_span(), outer_span)
            with self.trace.start_as_current_span("inner_span") as inner_span:
                self.assertNotEqual(outer_span, inner_span)
                self.assertEqual(get_current_span(), inner_span)
            # After exiting inner, context should revert to outer
            self.assertEqual(get_current_span(), outer_span)

    def test_get_current_span_success_and_failure(self):
        """Test getting the current span inside and outside a context."""
        # Failure case
        with self.assertRaisesRegex(Exception, "No active span context found."):
            get_current_span()

        # Success case
        with self.trace.start_as_current_span("test_span") as span:
            self.assertEqual(get_current_span(), span)

    def test_get_current_llm_span(self):
        """Test getting an LLM span, including failure cases."""
        # Failure case 1: No span active
        with self.assertRaisesRegex(Exception, "No active span context found."):
            get_current_span(span_type=SpanType.LLM)

        # Failure case 2: Active span is not an LLM span
        with self.trace.start_as_current_span("not_llm_span", span_type=SpanType.LOGIC):
            with self.assertRaisesRegex(
                Exception, "Expected span of type llm, but got logic"
            ):
                get_current_span(span_type=SpanType.LLM)

        # Success case
        with self.trace.start_as_current_span(
            "llm_span", span_type=SpanType.LLM
        ) as span:
            self.assertEqual(get_current_span(span_type=SpanType.LLM), span)

    def test_llm_span_creation(self):
        """Verify a span with SpanType.LLM is an instance of LLMSpan."""
        with self.trace.start_as_current_span(
            "test_llm", span_type=SpanType.LLM
        ) as span:
            self.assertIsInstance(span, LLMSpan)
            self.assertEqual(span.span_type, SpanType.LLM)

    def test_generic_span_creation(self):
        """Verify that LOGIC and TOOL spans are instances of the base Span class."""
        with self.trace.start_as_current_span(
            "test_logic", span_type=SpanType.LOGIC
        ) as span:
            self.assertIsInstance(span, Span)
            self.assertNotIsInstance(span, LLMSpan)
            self.assertEqual(span.span_type, SpanType.LOGIC)

        with self.trace.start_as_current_span(
            "test_tool", span_type=SpanType.TOOL
        ) as span:
            self.assertIsInstance(span, Span)
            self.assertNotIsInstance(span, LLMSpan)
            self.assertEqual(span.span_type, SpanType.TOOL)


if __name__ == "__main__":
    unittest.main()
