# remember to load auth first!
from vals import Check, Run, SingleRunReview, Suite, Test
import asyncio


async def create_suite_example():
    suite = Suite(
        title="Jeopardy Knowledge Test Suite",
        description="Testing model knowledge with classic Jeopardy-style questions",
        global_checks=[
            Check(operator="grammar"),
        ],
        tests=[
            Test(
                input_under_test="This planet is known as the Red Planet.",
                checks=[
                    Check(operator="includes", criteria="Mars"),
                ],
            ),
            Test(
                input_under_test="This author wrote 'To Kill a Mockingbird'.",
                checks=[
                    Check(operator="includes", criteria="Harper Lee"),
                ],
            ),
            Test(
                input_under_test="This is the chemical symbol for gold.",
                checks=[
                    Check(operator="includes", criteria="Au"),
                ],
            ),
            Test(
                input_under_test="This country is home to Machu Picchu.",
                checks=[
                    Check(operator="includes", criteria="Peru"),
                ],
            ),
            Test(
                input_under_test="This is the largest ocean on Earth.",
                checks=[
                    Check(operator="includes", criteria="Pacific"),
                ],
            ),
            Test(
                input_under_test="This scientist developed the theory of relativity.",
                checks=[
                    Check(operator="includes", criteria="Einstein"),
                ],
            ),
            Test(
                input_under_test="This Shakespeare play features the characters Romeo and Juliet.",
                checks=[
                    Check(operator="includes", criteria="Romeo and Juliet"),
                ],
            ),
            Test(
                input_under_test="This is the capital city of France.",
                checks=[
                    Check(operator="includes", criteria="Paris"),
                ],
            ),
        ],
    )

    await suite.create()
    print(f"Created suite: {suite.title} (ID: {suite.id})")

    return suite


async def run_suite_example(suite: Suite):
    run = await suite.run(
        model="gpt-4o-mini",
        run_name="Jeopardy Knowledge Test Run",
        wait_for_completion=True,
    )

    print(f"Run completed: {run.name} (ID: {run.id})")
    print(f"Pass rate: {run.pass_rate:.2%}" if run.pass_rate else "Pass rate: N/A")
    print(f"Status: {run.status}")

    return run


async def add_to_queue_example(run: Run):
    await run.add_to_queue(number_of_reviews=2, rereview_auto_eval=True)

    print(f"Added run {run.id} to human review queue")
    print(f"Run review ID: {run.run_review_id}")


async def get_review_example(run: Run) -> SingleRunReview:
    assert run.run_review_id is not None

    review = await run.review

    print(f"Review status: {review.status}")
    print(f"Review created by: {review.created_by}")
    print(f"Review number of reviews: {review.number_of_reviews}")
    print(f"Review assigned reviewers: {review.assigned_reviewers}")
    print(f"# of reviewed tests: {len(await review.test_results)}")

    return review


async def modify_review_example(review: SingleRunReview) -> None:
    await review.modify_queue(assigned_reviewers=["jaret@vals.ai", "jarett+1@vals.ai"])

    print(f"Review modified: {review.assigned_reviewers}")


async def async_main():
    suite = await create_suite_example()
    run = await run_suite_example(suite)
    await add_to_queue_example(run)
    review = await get_review_example(run)
    await modify_review_example(review)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
