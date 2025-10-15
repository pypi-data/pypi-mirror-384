from datetime import datetime
from typing import ClassVar
from asyncstdlib import cached_property
from pydantic import BaseModel, field_validator, model_validator
from pydantic.fields import PrivateAttr
from vals.graphql_client.enums import (
    RunReviewStatusEnum,
    TemplateType,
    TestResultReviewStatusEnum,
)
from vals.graphql_client.input_types import TestReviewFilterOptionsInput
from vals.sdk.types import CheckResult, TestResult
from vals.sdk.util import get_ariadne_client, score_to_label

LIMIT = 200


class UnderDevelopment(Exception):
    DEFAULT_MESSAGE = (
        "This method is in the process of being changed and will be added back in soon."
    )

    def __init__(self, message: str = DEFAULT_MESSAGE):
        self.message = message


class SingleRunReview(BaseModel):
    id: str
    """
    Internal UUID for the run review
    """

    created_by: str
    """User who first added a test result to the queue"""

    _project_uuid: str = PrivateAttr()
    """Internal project uuid that is temporary"""

    _run_id: str = PrivateAttr()
    """Needed to fetch the run id that we want to pull results from"""

    created_at: datetime
    """Timestamp when the run review was created"""

    completed_time: datetime | None
    """Timestamp when the run review was completed"""

    # TODO: Convert the enum to a literal type
    status: RunReviewStatusEnum
    """
    Status of the run review

    - Pending
    - Archived
    - Completed
    """

    # Aggregated stats across all human reviews in the run
    agreement_rate_human_eval: float | None
    """
    Agreement rate between the human reviews across all test results.
    
    If not reviewing auto evals, this will be None.
    """

    pass_rate_human_eval: float | None
    """
    Pass rate across all human reviews.
    
    If not reviewing auto evals, this will be None.
    """

    agreement_rate_auto_eval: float | None
    """
    Agreement rate between the human reviews and the auto evals across all test results.
    
    If not reviewing auto evals, this will be None.
    """

    flagged_rate: float | None
    """
    Rate of flagged test results across all test results.
    
    If not reviewing auto evals, this will be None.
    """

    # Metadata assigned at run review creation
    number_of_reviews: int
    """
    Number of reviews that must be completed PER test result added to the run review.

    if number of reviews is 2 and we have 1 test result in queue, we will need 2 reviews to complete the run review.
    """

    assigned_reviewers: list[str]
    """
    List of reviewers assigned to the run review.
    """

    test_results: ClassVar[list["TestResultReview"]]

    @staticmethod
    async def _fetch_test_result_reviews(
        run_id: str,
    ) -> list["TestResultReview"]:
        client = get_ariadne_client()
        offset = 0
        all_test_result_reviews: list["TestResultReview"] = []

        while True:
            default_filter = {
                "status": TestResultReviewStatusEnum.COMPLETED,
                "limit": LIMIT,
                "offset": offset,
            }

            test_result_reviews_with_count = (
                await client.single_test_result_reviews_with_count(
                    run_id=run_id,
                    filter_options=TestReviewFilterOptionsInput(**default_filter),
                )
            )

            current_batch = test_result_reviews_with_count.test_result_reviews_with_count.single_test_results

            all_test_result_reviews.extend(
                [
                    TestResultReview(**test_result.model_dump())
                    for test_result in current_batch
                ]
            )

            total_count = (
                test_result_reviews_with_count.test_result_reviews_with_count.count
            )

            if len(all_test_result_reviews) >= total_count:
                break

            offset += LIMIT

        return all_test_result_reviews or []

    @classmethod
    async def from_id(cls, id: str, project_id: str) -> "SingleRunReview":
        client = get_ariadne_client()

        run_review_query = await client.get_single_run_review(
            run_review_id=id, project_id=project_id
        )
        run_review = run_review_query.single_run_review

        if run_review is None:
            raise ValueError(
                "Run review could not be found. Please ensure that run review still exists."
            )

        single_run_review = run_review.model_dump()

        if len(run_review.assigned_reviewers) == 0:  # -> default for all users selected
            user_options_query = await client.get_user_options(project_id=project_id)

            single_run_review["assigned_reviewers"] = list(
                set(user_options_query.user_emails)
            )

        single_run_review = SingleRunReview.model_validate(
            single_run_review, strict=False
        )

        single_run_review._project_uuid = run_review.project.id
        single_run_review._run_id = run_review.run.id

        return single_run_review

    @cached_property
    async def test_results(self) -> list["TestResultReview"]:
        """
        Exhaustive list of all test results that have been completed inside the run review.

        Currently do not support pending reviews.
        """

        return await self._fetch_test_result_reviews(self._run_id)

    async def modify_queue(
        self,
        assigned_reviewers: list[str],
    ) -> None:
        raise UnderDevelopment()

        client = get_ariadne_client()

        await client.add_or_remove_users_to_run_review(
            single_run_review_id=self.id,
            project_id=self._project_uuid,
            assigned_reviewers=assigned_reviewers,
        )

        self.assigned_reviewers = assigned_reviewers


class CustomReviewTemplate(BaseModel):
    name: str
    """Name of the review template"""

    instructions: str
    """Instructions for the reviewer"""

    optional: bool
    """Whether the review template is optional to fill out in the review"""


class NumericTemplate(CustomReviewTemplate):
    min_value: int
    """Minimum value user can select"""

    max_value: int
    """Maximum value user can select"""


class FreeTextTemplate(CustomReviewTemplate):
    pass


class CategoricalTemplate(CustomReviewTemplate):
    categories: list[str]
    """List of categories user can select from"""


def create_template(data: dict) -> "CustomReviewTemplate":
    template_type = data.get("type")

    match template_type:
        case TemplateType.NUMERICAL:
            return NumericTemplate(**data)
        case TemplateType.CATEGORICAL:
            return CategoricalTemplate(**data)
        case TemplateType.FREE_TEXT:
            return FreeTextTemplate(**data)
        case _:
            raise ValueError(
                f"Unsupported template type has been provided. {template_type}"
            )


class CustomReviewValue(BaseModel):
    template: CustomReviewTemplate
    """Template that the review was done from"""

    value: str
    """
    Value that the user selected when reviewing.

    Normalized to a string value.
    """

    @model_validator(mode="before")
    def create_template(cls, obj: dict):
        data = obj.copy()

        data["template"] = create_template(data["template"])

        return data


class ReviewedCheckResult(CheckResult):
    human_eval: str | bool | None
    """
    Human eval for a check in the review.

    - False -> Fail
    - True -> Pass
    - String -> Likert scale value

    - None -> Flagged
    """

    is_flagged: bool
    """
    Whether the test result was flagged by the reviewer.
    """

    @field_validator("is_flagged", mode="before")
    def validate_is_flagged(cls, v):
        if isinstance(v, bool):
            return v

        return False

    @field_validator("human_eval", mode="before")
    def validate_human_eval(cls, v):
        if isinstance(v, str):
            return v

        if isinstance(v, int):
            return v == 1

        return v

    @model_validator(mode="before")
    def map_fields(cls, obj):
        obj = obj.copy()

        check = CheckResult.model_validate(obj).model_dump()

        # If its a string that means we are using a likert scale, then the human eval needs to be mapped to the label too.
        # Just like the auto eval was
        if isinstance(check["auto_eval"], str):
            check["human_eval"] = score_to_label(
                obj["binary_human_eval"], obj["custom_operator"]["rubric"]
            )
        else:
            check["human_eval"] = obj.get("binary_human_eval", None)

        check["is_flagged"] = obj.get("is_flagged", False)

        return check


class ReviewedTestResult(BaseModel):
    id: str
    """
    Internal UUID for the test result review
    """

    feedback: str
    """Optional feedback from the reviewer on the test result they reviewed"""

    completed_by: str
    """User who completed the review"""

    completed_at: datetime
    """Timestamp when the review was completed"""

    started_at: datetime
    """Timestamp when the review was started"""

    created_by: str
    """User who added the test result to the queue"""

    status: TestResultReviewStatusEnum
    """Status of the review
    
    - Pending
    - Completed
    """

    reviewed_check_results: list[ReviewedCheckResult]
    """
    Metadata on the auto eval review for this test result.

    If not reviewing auto evals, this will be empty.
    """

    custom_review_values: list[CustomReviewValue]
    """
    Metadata on the custom review for this test result.

    If not reviewing with human review templates, this will be empty.
    """

    @model_validator(mode="before")
    def map_fields(cls, obj: dict):
        data = obj.copy()

        human_review_values = data.get("per_check_test_review", [])
        check_result_values = data.get("test_result", {}).get("result_json", {})

        if len(human_review_values) != len(check_result_values):
            raise ValueError(
                "There was an issue when saving the review which caused the number of human review values and checks to not match."
            )

        data["reviewed_check_results"] = [
            ReviewedCheckResult.model_validate({**human_eval, **check_result})
            for human_eval, check_result in zip(
                human_review_values, check_result_values
            )
        ]

        data["custom_review_values"] = [
            CustomReviewValue.model_validate(value)
            for value in data.get("custom_review_values", [])
        ]

        return data


class TestResultReview(TestResult):
    reviewed_by: list[str]
    """
    List of users who have reviewed the test result.

    Can only be > 1 if number of reviews is > 1.
    """

    reviews: list[ReviewedTestResult]
    """
    Metadata on reviews that users have completed for this test result.
    """

    @model_validator(mode="before")
    def map_fields(cls, obj: dict):
        data = obj.copy()

        # its easier to build off the test result model then create this from scratch
        template = TestResult.model_validate(data).model_dump()

        template["reviewed_by"] = data.get("reviewed_by", [])

        # Remove all pending reviews from the list TODO: Add this filter into the graphql query
        completed_reviews = [
            review
            for review in data.get("single_test_reviews", [])
            if review["status"] == TestResultReviewStatusEnum.COMPLETED
        ]

        template["reviews"] = [
            ReviewedTestResult.model_validate(value) for value in completed_reviews
        ]

        return template

    @property
    def review(self) -> "ReviewedTestResult":
        """Allows users to access just the first review, useful for if they know there is only one review per test result."""

        if len(self.reviews) == 0:
            raise ValueError("No reviews found for this test result.")

        return self.reviews[0]
