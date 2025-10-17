import asyncio

from arcade_tdk.errors import ToolExecutionError
from openai import OpenAI

from arcade_google_docs.docmd import DocMD
from arcade_google_docs.tools.edit_agent.models.planning import (
    Plan,
    ReasoningEffort,
    Step,
)
from arcade_google_docs.tools.edit_agent.progress_tracker import ExecutionProgressTracker
from arcade_google_docs.tools.edit_agent.prompts import PLAN_EDIT_DOCUMENT_SYSTEM_PROMPT


async def _generate_step_for_user_edit_request(
    openai_client: OpenAI,
    docmd: DocMD,
    user_edit_request: str,
    query_index: int,
    reasoning_effort: ReasoningEffort,
    progress: ExecutionProgressTracker,
) -> Step:
    """Generate a step for a single user edit request."""
    messages = [
        {"role": "developer", "content": PLAN_EDIT_DOCUMENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"{docmd}\n\nEDIT REQUEST:\n{user_edit_request}",
        },
    ]

    try:
        completion = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: openai_client.beta.chat.completions.parse(
                model="gpt-5-mini",
                messages=messages,  # type: ignore[arg-type]
                response_format=Step,
                reasoning_effort=reasoning_effort.value,  # type: ignore[arg-type]
            ),
        )
        step = completion.choices[0].message.parsed
    except Exception as e:
        progress.add(
            f"Failed to generate step for edit request {query_index + 1} '{user_edit_request}': {e}"
        )
        raise ToolExecutionError(
            message=(
                f"Failed to generate step for edit request {query_index + 1} '{user_edit_request}'"
            ),
            developer_message="\n".join(progress.get_messages()),
        )
    else:
        return step or Step(edit_items=[])


def _merge_steps(steps: list[Step]) -> Step:
    """Merge multiple steps into a single step."""
    merged_edit_items = []

    for step in steps:
        merged_edit_items.extend(step.edit_items)

    return Step(edit_items=merged_edit_items)


def _build_ordered_plan(merged_step: Step) -> Plan:
    """
    Convert a merged step into an ordered plan with content edits first,
    then all formatting/styling edits grouped into a single step at the end.
    """
    if not merged_step.edit_items:
        return Plan(steps=[])

    content_edits = []
    formatting_edits = []

    for i, edit_item in enumerate(merged_step.edit_items):
        if edit_item.edit_request_type.is_style_or_formatting_edit():
            formatting_edits.append((i, edit_item))
        else:
            content_edits.append((i, edit_item))

    # Sort content edits by precedence, maintaining original order for same precedence
    content_edits.sort(key=lambda x: (x[1].edit_request_type.get_precedence(), x[0]))

    steps = []

    for _, edit_item in content_edits:
        step = Step(edit_items=[edit_item])
        steps.append(step)

    if formatting_edits:
        formatting_items = [edit_item for _, edit_item in formatting_edits]
        formatting_step = Step(edit_items=formatting_items)
        steps.append(formatting_step)

    return Plan(steps=steps)


async def plan_edits(
    openai_client: OpenAI,
    docmd: DocMD,
    user_edit_requests: list[str],
    reasoning_effort: ReasoningEffort,
    progress: ExecutionProgressTracker,
) -> Plan:
    """
    Plan edits to a Google Docs document before actually executing them.
    Returns a plan with ordered steps for executing the edits.
    """
    # Generate a step for each user edit request in parallel
    step_tasks = [
        _generate_step_for_user_edit_request(
            openai_client,
            docmd,
            user_edit_request,
            i,
            reasoning_effort,
            progress,
        )
        for i, user_edit_request in enumerate(user_edit_requests)
    ]
    steps = await asyncio.gather(*step_tasks)

    merged_step = _merge_steps(steps)
    plan = _build_ordered_plan(merged_step)

    return plan
