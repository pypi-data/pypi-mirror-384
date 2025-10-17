from typing import Annotated

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Google
from openai import OpenAI

from arcade_google_docs.tools.edit_agent.executor import execute_plan
from arcade_google_docs.tools.edit_agent.models.planning import ReasoningEffort
from arcade_google_docs.tools.edit_agent.planner import plan_edits
from arcade_google_docs.tools.edit_agent.progress_tracker import ExecutionProgressTracker
from arcade_google_docs.tools.edit_agent.utils import get_docmd
from arcade_google_docs.utils import build_docs_service


@tool(
    requires_auth=Google(
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
        ],
    ),
    requires_secrets=["OPENAI_API_KEY"],
)
async def edit_document(
    context: ToolContext,
    document_id: Annotated[str, "The ID of the document to edit"],
    edit_requests: Annotated[
        list[str],
        "A list of natural language descriptions of the desired change(s) to the document. "
        "Each entry should be a single, self-contained edit request that can be fully understood "
        "independently. Note: Each request may result in zero, one, or multiple actual edits "
        "depending on what changes are needed (e.g., a request might be ignored if the change "
        "already exists in the document).",
    ],
    reasoning_effort: Annotated[
        ReasoningEffort, "The effort to put into reasoning about the edit(s). Defaults to medium"
    ] = ReasoningEffort.MEDIUM,
) -> Annotated[dict, "The edited document's title, documentId, and documentUrl in a dictionary"]:
    """
    Edit a Google Docs document with the specified edit request.

    This tool does not have context about previous edits because it is stateless. If your edit
    request depends on knowledge about previous edits, then you should provide that context in
    the edit requests.
    """
    progress = ExecutionProgressTracker()
    progress.add(f"Starting to create a plan with '{reasoning_effort.value}' reasoning effort")

    openai_client = OpenAI(api_key=context.get_secret("OPENAI_API_KEY"))
    google_service = build_docs_service(context.get_auth_token_or_empty())
    docmd = get_docmd(google_service, document_id)

    plan = await plan_edits(openai_client, docmd, edit_requests, reasoning_effort, progress)

    result = await execute_plan(openai_client, google_service, docmd, document_id, plan, progress)

    return result
