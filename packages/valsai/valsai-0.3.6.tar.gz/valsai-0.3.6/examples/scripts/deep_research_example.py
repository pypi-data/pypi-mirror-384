"""Run a Deep Research model from the SDK.

Prerequisites:
- VALS_API_KEY exported in your environment.
- A suite ID you have access to.

Usage:
    uv run python sdk/examples/scripts/deep_research_example.py --suite-id <SUITE_ID> \
        --prompt "What are the biggest challenges in fusion energy commercialization?" \
        --model openai/o3-deep-research-2025-06-26 --wait
"""

from __future__ import annotations

import argparse
import asyncio
import json

from vals.sdk.suite import Suite
from vals.sdk.types import RunParameters


async def run_deep_research(
    suite_id: str,
    prompt: str,
    model: str,
    wait: bool,
) -> None:
    suite = await Suite.from_id(suite_id)

    parameters = RunParameters(
        temperature=0.7,
        max_output_tokens=4096,
        system_prompt=prompt,
        custom_parameters={
            "background": True,
            "reasoning": {"summary": "auto"},
            "tools": [
                {"type": "web_search_preview"},
                {
                    "type": "code_interpreter",
                    "container": {"type": "auto", "file_ids": []},
                },
            ],
        },
    )

    # Trigger a live run. The prompt is written into the suite's system prompt.
    run = await suite.run(
        model=model,
        parameters=parameters,
        run_name="Deep Research Example",
        wait_for_completion=False,
    )

    print(f"Started run {run.id} with model {model}")
    print("Custom parameters: ")
    print(json.dumps(run.parameters.custom_parameters, indent=2))

    if wait:
        status = await run.wait_for_run_completion()
        print(f"Run completed with status {status}")

        await run.pull()
        qa_pairs = await run.get_qa_pairs(remaining_limit=1)
        if qa_pairs:
            output_context = qa_pairs[0].output_context or {}
            deep_research_meta = output_context.get("deep_research")
            if deep_research_meta:
                print("\nFirst QA pair deep research metadata:")
                print(json.dumps(deep_research_meta, indent=2)[:2000])
            else:
                print("\nNo deep research metadata found on first QA pair yet.")
        else:
            print("No QA pairs available yet.")


async def main():
    parser = argparse.ArgumentParser(
        description="Run a Deep Research example via the SDK"
    )
    parser.add_argument("--suite-id", required=True, help="Suite identifier to run")
    parser.add_argument(
        "--prompt",
        default="Summarize the latest challenges in deploying fusion energy at utility scale.",
        help="Prompt to use as the system message",
    )
    parser.add_argument(
        "--model",
        default="openai/o3-deep-research-2025-06-26",
        help="Model identifier (must support Deep Research)",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Block until the run completes and fetch the first QA pair metadata",
    )
    args = parser.parse_args()

    await run_deep_research(
        suite_id=args.suite_id,
        prompt=args.prompt,
        model=args.model,
        wait=args.wait,
    )


if __name__ == "__main__":
    asyncio.run(main())
