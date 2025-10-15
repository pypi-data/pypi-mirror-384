import asyncio
import json
from datetime import datetime
from typing import Any, ClassVar

import aiohttp
import pandas as pd
from asyncstdlib import cached_property
from pydantic import BaseModel, PrivateAttr

from vals.graphql_client import Client, PullRunRunCustomMetrics
from vals.graphql_client.enums import RunStatus
from vals.sdk.auth import _get_auth_token, be_host, fe_host
from vals.sdk.exceptions import ValsException
from vals.sdk.inspect_wrapper import InspectWrapper
from vals.sdk.run_review import SingleRunReview, UnderDevelopment
from vals.sdk.types import (
    ModelCustomOperatorFunctionType,
    ModelFunctionType,
    QuestionAnswerPair,
    RunMetadata,
    RunParameters,
    Test,
    TestResult,
)
from vals.sdk.util import get_ariadne_client


class Run(BaseModel):
    id: str
    """Unique identifier for the run."""

    project_id: str
    """Project ID of the run."""

    _project_uuid: str = PrivateAttr()
    """Temporary project uuid for internal use."""

    name: str
    """Name of the run."""

    qa_set_id: str | None
    """Unique identifier for the QA set run was created with."""

    test_suite_id: str
    """Unique identifier for the test suite run was created with."""

    test_suite_title: str
    """Title of the test suite run was created with."""

    model: str
    """Model used to perform the run."""

    pass_percentage: float | None
    """Average pass percentage of all tests."""

    pass_rate: float | None
    """Percentage of checks that passed"""

    pass_rate_error: float | None
    """Error margin for pass rate"""

    success_rate: float | None
    """Number of tests where all checks passed"""

    success_rate_error: float | None
    """Error margin for success rate"""

    custom_metrics: list[PullRunRunCustomMetrics]

    status: RunStatus
    """Status of the run"""

    archived: bool
    """Whether the run has been archived"""

    text_summary: str
    """Automatically generated summary of common error modes for the run."""

    timestamp: datetime
    """Timestamp of when the run was created."""

    completed_at: datetime | None
    """Timestamp of when the run was completed."""

    parameters: RunParameters
    """Parameters used to create the run."""

    run_review_id: str | None
    """ID of the run review for the run."""

    test_results: list[TestResult]
    """List of test results for the run."""

    review: ClassVar[SingleRunReview]

    _client: Client = PrivateAttr(default_factory=get_ariadne_client)

    @staticmethod
    async def _create_from_pull_result(run_id: str, client: Client) -> "Run":
        """Helper method to create a Run instance from a pull_run query result"""

        result = await client.pull_run(run_id)

        offset = 0
        page_size = 200
        test_results = []
        exists_test_results_left_to_pull = True
        while exists_test_results_left_to_pull:
            test_result_query = await client.pull_test_results_with_count(
                run_id=run_id, offset=offset, limit=page_size
            )
            test_results.extend(
                [
                    TestResult.from_graphql(test_result)
                    for test_result in test_result_query.test_results_with_count.test_results
                ]
            )
            offset += page_size
            exists_test_results_left_to_pull = (
                len(test_result_query.test_results_with_count.test_results) >= page_size
            )

        # Map maximum_threads to parallelism for backwards compatibility
        parameters_dict = result.run.parameters.model_dump()
        model = parameters_dict.pop("model_under_test", "")

        if "maximum_threads" in parameters_dict:
            parameters_dict["parallelism"] = parameters_dict.pop("maximum_threads")
        parameters = RunParameters(**parameters_dict)

        run_review_id = None
        if result.run.run_review:
            run_review_id = result.run.run_review.id

        run = Run(
            id=run_id,
            run_review_id=run_review_id,
            project_id=result.run.project.slug,
            name=result.run.name,
            qa_set_id=result.run.qa_set.id if result.run.qa_set else None,
            model=model,
            pass_percentage=(
                result.run.pass_percentage * 100
                if result.run.pass_percentage is not None
                else None
            ),
            pass_rate=result.run.pass_rate.value if result.run.pass_rate else None,
            pass_rate_error=(
                result.run.pass_rate.error if result.run.pass_rate else None
            ),
            success_rate=(
                result.run.success_rate.value if result.run.success_rate else None
            ),
            success_rate_error=(
                result.run.success_rate.error if result.run.success_rate else None
            ),
            custom_metrics=result.run.custom_metrics,
            status=result.run.status,
            archived=result.run.archived,
            text_summary=result.run.text_summary,
            timestamp=result.run.timestamp,
            completed_at=result.run.completed_at,
            parameters=parameters,
            test_results=test_results,
            test_suite_title=result.run.test_suite.title,
            test_suite_id=result.run.test_suite.id,
        )

        run._project_uuid = result.run.project.id

        return run

    @classmethod
    async def list_runs(
        cls,
        limit: int = 25,
        offset: int = 0,
        suite_id: str | None = None,
        show_archived: bool = False,
        search: str = "",
        project_id: str = "default-project",
    ) -> list["RunMetadata"]:
        """List runs associated with this organization

        Args:
            limit: Maximum number of runs to return
            offset: Number of runs to skip
            suite_id: Filter by specific suite ID
            show_archived: Include archived runs
            search: Search string for filtering runs
            project_id: Optional project ID to filter runs by project
        """
        client = get_ariadne_client()
        result = await client.list_runs(
            limit=limit,
            offset=offset,
            suite_id=suite_id,
            archived=show_archived,
            search=search,
            project_id=project_id,
        )
        return [
            RunMetadata.from_graphql(run) for run in result.runs_with_count.run_results
        ]

    @classmethod
    async def from_id(cls, run_id: str) -> "Run":
        """Pull most recent metadata and test results from the vals servers."""
        client = get_ariadne_client()
        return await cls._create_from_pull_result(run_id, client)

    @property
    def url(self) -> str:
        return f"{fe_host()}/project/{self.project_id}/results/{self.id}"

    def to_dict(self) -> dict[str, Any]:
        """Converts the run to a dictionary."""
        return self.model_dump(exclude_none=True, exclude_defaults=True, mode="json")

    async def to_json_file(self, file_path: str) -> None:
        """Converts the run to a JSON file."""
        with open(file_path, "w") as f:
            f.write(await self.to_json_string())

    async def pull(self) -> None:
        """Update this Run instance with latest data from vals servers."""

        updated = await self._create_from_pull_result(self.id, self._client)
        # TODO: There's probably a better way to update the object.
        for field in Run.model_fields:
            setattr(self, field, getattr(updated, field))

    async def get_qa_pairs(
        self, offset: int = 0, remaining_limit: int = 200
    ) -> list[QuestionAnswerPair]:
        """Get up to `remaining_limit` QA pairs for a run.
        set `remaining_limit = -1` to get all QA pairs."""
        qa_pairs = []
        current_offset = offset
        batch_size = 200

        while remaining_limit != 0:
            # Calculate the current batch size
            current_batch_size = (
                min(batch_size, remaining_limit) if remaining_limit > 0 else batch_size
            )

            result = await self._client.list_question_answer_pairs(
                qa_set_id=self.qa_set_id,
                offset=current_offset,
                limit=current_batch_size,
            )

            batch_results = [
                QuestionAnswerPair.from_graphql(graphql_qa_pair)
                for graphql_qa_pair in result.question_answer_pairs_with_count.question_answer_pairs
            ]

            qa_pairs.extend(batch_results)

            # If we got fewer results than requested, we've reached the end
            if len(batch_results) < current_batch_size:
                break

            # Update for next iteration
            current_offset += len(batch_results)
            remaining_limit -= len(batch_results)

        return qa_pairs

    async def run_status(self) -> RunStatus:
        """Get the status of a run"""
        result = await self._client.get_run_status(run_id=self.id)
        self.status = result.run.status
        return self.status

    async def wait_for_run_completion(
        self,
    ) -> RunStatus:
        """
        Block a process until a given run has finished running.

        Returns the status of the run after completion.
        """
        await asyncio.sleep(1)

        status = await self.run_status()

        completed_statuses = [
            RunStatus.SUCCESS,
            RunStatus.ERROR,
            RunStatus.CANCELLED,
            RunStatus.PAUSE,
        ]

        while status not in completed_statuses:
            status = await self.run_status()
            await asyncio.sleep(3)  # Poll every 3 seconds
        return status

    async def to_csv_string(self) -> str:
        """Same as to_csv, but returns a string instead of writing to a file."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{be_host()}/export_results_to_file/?run_id={self.id}",
                headers={"Authorization": _get_auth_token()},
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValsException(
                        "Received Error from Vals Servers: " + error_text
                    )
                return await response.text()

    async def to_json_string(self) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{be_host()}/export_run_to_json/?run_id={self.id}",
                headers={"Authorization": _get_auth_token()},
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValsException(
                        "Received Error from Vals Servers: " + error_text
                    )
                return await response.text()

    async def to_csv(self, file_path: str) -> None:
        """Get the CSV results of a run, as bytes."""
        with open(file_path, "w") as f:
            f.write(await self.to_csv_string())

    async def retry_failing_tests(self) -> None:
        """Retry all failing tests in a run."""

        await self._client.rerun_tests(run_id=self.id)

    async def resume_run(
        self,
        model: str
        | ModelFunctionType
        | list[QuestionAnswerPair]
        | InspectWrapper
        | None = None,
        wait_for_completion: bool = False,
        upload_concurrency: int = 3,
        custom_operators: list[ModelCustomOperatorFunctionType] | None = None,
        parallelism: int | None = None,
    ) -> None:
        """Resume a run that was paused.

        This method will:
        1. Check for existing QA pairs that haven't been auto-evaluated
        2. Check for existing completed test results
        3. Run the remaining tests that haven't been processed yet
        """
        if model is None:
            model = self.model

        if custom_operators is None:
            custom_operators = []

        if parallelism is not None:
            self.parameters.parallelism = parallelism

        # Import Suite here to avoid circular import
        from vals.sdk.suite import Suite

        suite = await Suite.from_id(self.test_suite_id)

        query_result = await self._client.unfinished_tests(run_id=self.id)
        unfinished_tests = [
            Test.model_validate(test.model_dump())
            for test in query_result.unfinished_tests.unfinished_tests
        ]

        completed_qa_pairs = await self.get_qa_pairs(
            offset=0, remaining_limit=query_result.unfinished_tests.test_suite_size
        )

        # Run the remaining tests, including existing QA pairs
        await self._client.update_run_status(
            run_id=self.id, status=RunStatus.IN_PROGRESS
        )
        await suite.run(
            model=model,
            model_name=self.model,
            run_name=self.name,
            wait_for_completion=wait_for_completion,
            parameters=self.parameters,
            upload_concurrency=upload_concurrency,
            custom_operators=custom_operators,
            eval_model_name=self.parameters.eval_model,
            run_id=self.id,
            qa_set_id=self.qa_set_id,
            remaining_tests=unfinished_tests,
            uploaded_qa_pairs=completed_qa_pairs,
        )

    async def pause_run(self):
        """Pause run."""
        result = await self._client.stop_run(run_id=self.id, status=RunStatus.PAUSE)
        if result.stop_run and not result.stop_run.success:
            raise Exception(f"Failed to pause run {self.id}")

    async def cancel_run(self):
        """Cancel run."""
        result = await self._client.stop_run(run_id=self.id, status=RunStatus.CANCELLED)
        if result.stop_run and not result.stop_run.success:
            raise Exception(f"Failed to cancel run {self.id}")

    async def rerun_all_checks(self, parameters: RunParameters | None = None) -> "Run":
        """
        Rerun all checks for a run, using existing QA pairs.
        returns a new Run object, rather than modifying the existing one.
        """

        # Import Suite here to avoid circular import
        from vals.sdk.suite import Suite

        if not parameters:
            parameters = self.parameters

        qa_pairs = await self.get_qa_pairs(offset=0, remaining_limit=-1)
        suite = await Suite.from_id(self.test_suite_id)
        return await suite.run(qa_pairs, parameters=parameters)

    @staticmethod
    async def get_status_from_id(run_id: str) -> RunStatus:
        """Get the status of a run directly from its ID without instantiating a Run object."""
        client = get_ariadne_client()
        result = await client.get_run_status(run_id=run_id)
        return result.run.status

    async def add_to_queue(
        self,
        template_ids: list[str] = [],
        assigned_reviewers: list[str] = [],
        number_of_reviews: int = 1,
        rereview_auto_eval: bool = True,
    ) -> None:
        raise UnderDevelopment()

        client = get_ariadne_client()

        run_review = await client.add_all_tests_to_queue_single(
            run_id=self.id,
            project_id=self._project_uuid,
            template_ids=template_ids,
            assigned_reviewers=assigned_reviewers,
            number_of_reviews=number_of_reviews,
            rereview_auto_eval=rereview_auto_eval,
        )

        self.run_review_id = (
            run_review.add_all_single_test_review_to_queue.single_run_review.id  # type: ignore
        )

    @cached_property
    async def review(self) -> SingleRunReview:
        """
        Get the review for a run.

        Will raise a ValueError if no review has been created for the run.
        """
        review_id = self.run_review_id
        project_id = self.project_id

        if review_id is None:
            raise ValueError(
                "No run review has been created for this run. Please start the review process before trying to get the review."
            )

        return await SingleRunReview.from_id(review_id, project_id)

    @classmethod
    async def get_run_dataframe(cls, run_id: str) -> pd.DataFrame:
        """Get a dataframe of the run results."""
        client = get_ariadne_client()
        result = await client.get_run_dataframe(run_id=run_id)
        rows = result.get_run_dataframe
        if not rows:
            raise Exception(
                "Failed to get run dataframe, ensure the run exists and was successfull."
            )

        # Convert each GraphQL object to a dict
        parsed_rows = []
        for row in rows:
            row_dict = row.__dict__.copy()

            # Convert stringified JSON to actual dict
            modifiers = json.loads(row_dict.get("modifiers", "{}"))
            row_dict.pop("modifiers", None)  # Remove the JSON string
            row_dict.update(
                {f"modifiers.{k}": v for k, v in modifiers.items()}
            )  # Flatten

            # Convert input/output_context from string to dict
            for context_field in ["input_context", "output_context"]:
                if context_field in row_dict:
                    try:
                        row_dict[context_field] = json.loads(row_dict[context_field])
                    except json.JSONDecodeError:
                        row_dict[context_field] = {}

            parsed_rows.append(row_dict)

        df = pd.DataFrame(parsed_rows)
        return df

    @classmethod
    async def update_custom_metric_result(
        cls,
        run_id: str,
        local: bool,
        custom_metric_result: float,
        custom_metric_id: str | None = None,
        custom_metric_name: str | None = None,
    ) -> str:
        """
        Update the result of a custom metric for a run.
        """
        client = get_ariadne_client()
        result = await client.update_custom_metric_result(
            run_id=run_id,
            local=local,
            custom_metric_result=custom_metric_result,
            custom_metric_id=custom_metric_id,
            custom_metric_name=custom_metric_name,
        )
        if not result.update_custom_metric_result:
            raise Exception(f"Failed to update custom metric result for run {run_id}")
        return result.update_custom_metric_result.id
