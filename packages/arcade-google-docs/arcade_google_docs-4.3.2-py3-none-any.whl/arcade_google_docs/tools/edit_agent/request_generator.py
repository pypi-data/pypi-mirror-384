import asyncio
import json
from typing import Literal

from arcade_tdk.errors import ToolExecutionError
from openai import OpenAI
from pydantic import BaseModel

from arcade_google_docs.docmd import DocMD
from arcade_google_docs.tools.edit_agent.models.planning import EditItem, Step
from arcade_google_docs.tools.edit_agent.prompts import (
    DETERMINE_BLOCK_ID_SYSTEM_PROMPT,
    ERROR_FEEDBACK_PROMPT,
    GENERATE_EDIT_REQUEST_SYSTEM_PROMPT,
    GENERATE_EDIT_REQUEST_SYSTEM_PROMPT_WITH_LOCATION_TAGS,
)


def _determine_block_id(openai_client: OpenAI, docmd: DocMD, edit_instruction: str) -> str:
    """Determine the block id that the edit instruction is targeting."""

    class ValidBlockIds(BaseModel):
        block_id: Literal[tuple(docmd.block_ids)]  # type: ignore[valid-type]

    completion = openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": DETERMINE_BLOCK_ID_SYSTEM_PROMPT},
            {"role": "user", "content": f"{docmd}\n\nEDIT REQUEST:\n{edit_instruction}"},
        ],
        response_format=ValidBlockIds,
    )
    parsed_response = completion.choices[0].message.parsed
    if not parsed_response:
        raise ToolExecutionError("Failed to determine a block id from the edit instruction")
    return str(parsed_response.block_id)


async def _generate_api_request_for_edit_item(
    openai_client: OpenAI,
    docmd: DocMD,
    edit_item: EditItem,
    previous_error: str | None = None,
    failed_requests: list[dict] | None = None,
) -> dict | None:
    """Generate a single edit request asynchronously.

    Returns a request dictionary for the batchUpdate endpoint or None
    """
    edit_instruction = edit_item.edit_instruction
    edit_request_type = edit_item.edit_request_type
    edit_item_thoughts = edit_item.thoughts

    messages = []
    if edit_request_type.is_location_based():
        # Run blocking operation in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        block_id = await loop.run_in_executor(
            None, _determine_block_id, openai_client, docmd, edit_instruction
        )
        annotated_docmd = docmd.get_docmd_with_annotated_block(block_id).to_string()
        messages.extend([
            {
                "role": "developer",
                "content": GENERATE_EDIT_REQUEST_SYSTEM_PROMPT_WITH_LOCATION_TAGS,
            },
            {
                "role": "user",
                "content": (
                    "DOCUMENT:\n"
                    f"{annotated_docmd}\n\n"
                    "THOUGHTS THAT OCCURRED WHEN CONSTRUCTING YOUR INSTRUCTIONS:\n"
                    f"{edit_item_thoughts}\n\n"
                    "YOUR JOB IS TO CONSTRUCT A SINGLE EDIT REQUEST OBJECT THAT SATISFIES "
                    "THE FOLLOWING INSTRUCTIONS:\n"
                    f"{edit_instruction}"
                ),
            },
        ])
    else:
        messages.extend([
            {"role": "developer", "content": GENERATE_EDIT_REQUEST_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "DOCUMENT:\n"
                    f"{docmd.to_string()}\n\n"
                    "THOUGHTS THAT OCCURRED WHEN CONSTRUCTING YOUR INSTRUCTIONS:\n"
                    f"{edit_item_thoughts}\n\n"
                    "YOUR JOB AND SOLE PURPOSE IS TO CONSTRUCT A SINGLE EDIT REQUEST "
                    "OBJECT THAT SATISFIES THE FOLLOWING INSTRUCTIONS:\n"
                    f"{edit_instruction}"
                ),
            },
        ])

    if previous_error and failed_requests:
        error_feedback = ERROR_FEEDBACK_PROMPT.format(
            error=previous_error, failed_requests=json.dumps(failed_requests, indent=2)
        )
        messages.append({"role": "assistant", "content": "I failed to edit the document."})
        messages.append({"role": "user", "content": error_feedback})

    # Run OpenAI API call in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    completion = await loop.run_in_executor(
        None,
        lambda: openai_client.beta.chat.completions.parse(
            model="gpt-5",
            messages=messages,  # type: ignore[arg-type]
            response_format=edit_request_type.get_request_model(),
            reasoning_effort="minimal",  # type: ignore[arg-type]
        ),
    )

    request = completion.choices[0].message.parsed
    if request:
        return {edit_request_type.value: request.model_dump(exclude_none=True)}
    return None


async def generate_api_request_for_step(
    openai_client: OpenAI,
    docmd: DocMD,
    step: Step,
    previous_error: str | None = None,
    failed_requests: list[dict] | None = None,
) -> list[dict]:
    """Generate edit requests for a single step.

    Returns a list of request dictionaries for the Google batchUpdate endpoint
    """
    if not step.edit_items:
        return []

    # Generate requests for all edit items in the step in parallel
    tasks = []
    for edit_item in step.edit_items:
        task = _generate_api_request_for_edit_item(
            openai_client,
            docmd,
            edit_item,
            previous_error,
            failed_requests,
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    return [result for result in results if result is not None]
