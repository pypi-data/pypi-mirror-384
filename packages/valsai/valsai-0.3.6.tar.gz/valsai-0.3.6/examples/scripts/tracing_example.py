"""
A comprehensive example demonstrating the vals.sdk.tracing module
in the context of a simple Retrieval-Augmented Generation (RAG) agent.
"""

import asyncio
import os

from vals import configure_credentials
from vals.sdk.tracing import (
    SpanLevel,
    SpanType,
    get_client,
    get_current_span,
)

# Configure credentials using the VALS_API_KEY environment variable.
configure_credentials(api_key=os.environ.get("VALS_API_KEY", "YOUR_VALS_API_KEY"))

# Get a trace client for the application.
trace = get_client("rag-agent-example")


@trace.span
def preprocess_query(query: str) -> str:
    """A simple synchronous function to show basic automatic tracing."""
    print(f"Preprocessing query: '{query}'")
    return query.strip().lower()


def log_retrieval_stats(doc_count: int):
    """
    A nested helper that demonstrates get_current_span.
    It accesses its parent span ('retrieve_documents') to add metadata.
    """
    try:
        # get_current_span() retrieves the currently active span from the context.
        parent_span = get_current_span()
        parent_span.update(metadata={"documents_retrieved": doc_count})
        print("Successfully updated parent span with retrieval stats.")
    except Exception as e:
        print(f"Could not get current span: {e}")


@trace.span(span_type=SpanType.TOOL)
async def retrieve_documents(processed_query: str) -> list[str]:
    """
    An async function representing a tool call to retrieve documents.
    This function now includes a nested span to demonstrate multi-level tracing.
    """
    print(f"Retrieving documents for: '{processed_query}'")

    # This demonstrates a nested span within a decorated function, creating a hierarchy.
    with trace.start_as_current_span("query_vector_db") as db_span:
        db_span.update(input={"query": processed_query, "top_k": 2})
        await asyncio.sleep(0.2)  # Simulate network I/O to a vector DB
        documents = [
            "Kazakhstan is the world's largest landlocked country by land area.",
            "The capital city of Kazakhstan is Astana.",
        ]
        db_span.update(output={"retrieved_doc_count": len(documents)})

    # This nested call demonstrates updating the parent span (`retrieve_documents`)
    # from a child function.
    log_retrieval_stats(len(documents))
    return documents


async def generate_response(query: str, context: list[str]) -> str:
    """
    The core LLM call, demonstrating manual span creation for fine-grained control.
    """
    # Use the context manager for manual control over a span's lifecycle.
    with trace.start_as_current_span(
        "generate_response_llm", span_type=SpanType.LLM
    ) as llm_span:
        print("Generating response with LLM...")
        prompt = f"Query: {query}\nContext: {' '.join(context)}"

        # The LLMSpan's update method accepts LLM-specific attributes.
        llm_span.update(
            input=prompt,
            model="openai/gpt-4-turbo",
            metadata={"provider": "openai"},
        )

        await asyncio.sleep(0.3)  # Simulate LLM API latency
        response = "Based on the context, Kazakhstan is the largest landlocked country and its capital is Astana."
        reasoning = "The model synthesized the provided context to answer the query about Kazakhstan."

        # Use the overloaded get_current_span to retrieve the LLMSpan safely.
        # This demonstrates how to access the span within the same context it was created.
        current_llm_span = get_current_span(span_type=SpanType.LLM)
        current_llm_span.update(
            output=response,
            usage={
                "in_tokens": len(prompt.split()),
                "out_tokens": len(response.split()),
                "reasoning_tokens": len(reasoning.split()),
            },
            reasoning=reasoning,
        )
        return response


@trace.span
def function_that_fails():
    """
    A function designed to fail to demonstrate automatic error capturing.
    The @trace.span decorator will automatically set the span's level to ERROR
    and record the exception details.
    """
    print("Running a function that is expected to fail...")
    raise ValueError("This is an intentional error for demonstration.")


@trace.span
async def run_rag_agent(query: str):
    """
    The main agent orchestrator that calls all the components.
    This shows how automatic and manual tracing can be mixed.
    """
    print(f"\n--- Running RAG Agent for query: '{query}' ---")

    # Use a manual span for a specific, non-functional block of code.
    with trace.start_as_current_span("planning") as planning_span:
        planning_span.update(
            input=query,
            output={"steps": ["preprocess", "retrieve", "generate"]},
            level=SpanLevel.INFO,
        )

    processed_query = preprocess_query(query)
    documents = await retrieve_documents(processed_query)
    await generate_response(query, documents)

    # We call the failing function within a try...except block.
    # The span for `function_that_fails` will be marked as an error,
    # but the exception is caught here, allowing the agent to continue.
    try:
        function_that_fails()
    except ValueError:
        print(
            "Caught expected error. The trace will reflect this failure, but the agent can proceed."
        )

    print("--- RAG Agent finished ---")


async def main():
    """Runs the agent and ensures traces are exported."""
    await run_rag_agent("Tell me about Kazakhstan.")

    # For this script, we add a small delay to ensure the background
    # processor has time to send all traces before the program exits.
    print("\nWaiting for traces to be exported...")
    await asyncio.sleep(2)
    print("All examples complete. Check the Vals platform for the trace.")


if __name__ == "__main__":
    asyncio.run(main())
