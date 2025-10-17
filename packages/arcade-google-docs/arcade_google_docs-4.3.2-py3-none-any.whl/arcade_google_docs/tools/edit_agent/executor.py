"""Execution service for the edit agent."""

from typing import Any

from arcade_tdk.errors import ToolExecutionError
from openai import OpenAI

from arcade_google_docs.docmd import DocMD
from arcade_google_docs.tools.edit_agent.models.planning import Plan
from arcade_google_docs.tools.edit_agent.progress_tracker import ExecutionProgressTracker
from arcade_google_docs.tools.edit_agent.request_generator import generate_api_request_for_step
from arcade_google_docs.tools.edit_agent.utils import get_docmd


async def execute_plan(
    openai_client: OpenAI,
    google_service: Any,
    docmd: DocMD,
    document_id: str,
    plan: Plan,
    progress: ExecutionProgressTracker,
) -> dict:
    """
    Execute a plan step by step.

    Returns a dictionary with responses, edit_requests, and execution_logs.
    """
    if plan.number_of_steps == 0:
        progress.add("I was unable to come up with a plan to edit the document")
        return {
            "responses": [],
            "edit_requests": [],
            "execution_logs": progress.get_messages(),
        }

    progress.add(
        f"I have a {plan.number_of_steps} step plan where I will perform "
        f"{plan.number_of_edit_requests} edit(s)"
    )
    progress.add(f"I need to execute the following plan:\n{plan.to_log_string()}")

    progress.add("Starting to execute on the plan...")
    all_google_edit_responses = []
    all_requests = []

    # Execute the plan step by step. Within each step, execute all items in parallel
    for step_num, step in enumerate(plan.steps):
        progress.add_step_start(step_num, len(plan.steps))

        # Refresh document state before each step (except the first one)
        if step_num > 0:
            docmd = get_docmd(google_service, document_id)

        step_requests = await generate_api_request_for_step(
            openai_client,
            docmd,
            step,
        )

        error: str | None = None
        failed_requests = step_requests

        for attempt in range(2):
            try:
                if attempt == 1:
                    # Regenerate on retry with error context
                    step_requests = await generate_api_request_for_step(
                        openai_client,
                        docmd,
                        step,
                        previous_error=error,
                        failed_requests=failed_requests,
                    )

                # All requests in the step are sent in a single batchUpdate call
                if step_requests:
                    google_edit_response = (
                        google_service.documents()
                        .batchUpdate(documentId=document_id, body={"requests": step_requests})
                        .execute()
                    )
                    all_google_edit_responses.append(google_edit_response)
                    all_requests.extend(step_requests)

                progress.add_step_success(step_num, len(plan.steps))
                break
            except Exception as e:
                progress.add_step_error(step_num, len(plan.steps), e)
                if attempt == 0:
                    error = str(e)
                    failed_requests = step_requests
                    progress.add_step_retry(step_num, len(plan.steps))
                    continue
                raise ToolExecutionError(
                    message=f"Failed to execute step {step_num + 1} after 2 attempts",
                    developer_message="\n".join(progress.get_messages()),
                )

    return {
        "responses": all_google_edit_responses,
        "edit_requests": all_requests,
        "execution_logs": progress.get_messages(),
    }
