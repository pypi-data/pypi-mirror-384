import asyncio
import os

from vals import (
    Check,
    Suite,
    Test,
    configure_credentials,
)
from vals.sdk.custom_metric import CustomMetric
from vals.sdk.run import Run
from vals.sdk.types import RunParameters

configure_credentials(api_key=os.environ["VALS_API_KEY"])


async def get_run_dataframe():
    """
    Get the dataframe of a run in which custom metric are run against
    """
    print("\n--- Get Run Dataframe for Custom Metric ---\n")

    df = await Run.get_run_dataframe("your-run-id")

    print(df.columns)
    # analyze locally


async def custom_metric_update_past_results():
    """
    Updated a custom metric that was added to a test suite
    Updates the past results of runs that use this custom metric
    """
    print("\n--- Custom Metric Update Past Results ---\n")
    custom_metric = await CustomMetric.from_id("your-custom-metric-id")

    custom_metric.python_file_path = "path/to/new/custom_metric.py"

    # will rerun custom metric on past runs
    await custom_metric.update(update_past=True)

    # run results will be updated with the result
    run = await Run.from_id("your-run-id")
    print("Custom Metric Results:")
    for custom_metric in run.custom_metrics:
        print(custom_metric)


async def custom_metric_from_existing():
    """
    Run a custom metric that already exists on a test suite (results don't persist)
    """
    print("\n--- Custom Metric from Existing ---\n")
    custom_metric = await CustomMetric.from_id("your-custom-metric-id")

    # persist=True will add the result to the run
    result = await custom_metric.run("your-run-id", persist=True)

    print(result)


async def custom_metric_from_local():
    """
    Run a custom metric that exists locally on a test suite (results don't persist)
    """
    import pandas as pd

    async def custom_metric_function(df: pd.DataFrame) -> float:
        print("--- Dataframe ---")
        print(df["input"])
        return 46

    # persist=True will add the result to the run
    result = await CustomMetric.run_local(
        "your-run-id",
        "Local-01",
        custom_metric_function,
        persist=True,
    )
    print(f"Result: {result}")


async def custom_metric_from_scratch():
    """
    Create a test suite
    Create a custom metric
    Assign the custom metric to the test suite (results persist)
    Run the test suite
    """
    print("\n--- Custom Metric from Scratch ---\n")
    suite = Suite(
        title="Custom Metric Example Test Suite",
        global_checks=[Check(operator="is_concise")],
        tests=[
            Test(
                input_under_test="Cats or dogs?",
                checks=[Check(operator="is_not_hallucinating")],
            ),
        ],
    )
    await suite.create()

    # NOTE, no duplicate custom metric names allowed
    custom_metric = CustomMetric(
        name="Example Custom Metric",
        description="This is a custom metric.",
        python_file_path="examples/data_files/custom_metric.py",
    )
    await custom_metric.create()

    await suite.set_custom_metrics(
        [custom_metric]
    )  # persists, suite now has these custom metrics for future runs

    run = await suite.run(
        model="gpt-4o-mini",
        wait_for_completion=True,
        parameters=RunParameters(system_prompt="Keep your message under 10 words."),
    )

    print(f"Run URL: {run.url}")
    print(f"Pass percentage: {run.pass_percentage}")
    print("Custom Metric Results:")
    for custom_metric in run.custom_metrics:
        print(custom_metric)


async def all():
    await get_run_dataframe()
    await custom_metric_update_past_results()
    await custom_metric_from_existing()
    await custom_metric_from_local()
    await custom_metric_from_scratch()


if __name__ == "__main__":
    asyncio.run(all())
