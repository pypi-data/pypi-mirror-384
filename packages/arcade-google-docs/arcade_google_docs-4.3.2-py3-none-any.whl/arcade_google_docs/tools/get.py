from typing import Annotated

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Google

from arcade_google_docs.docmd import build_docmd
from arcade_google_docs.models.document import Document
from arcade_google_docs.utils import build_docs_service


# Uses https://developers.google.com/docs/api/reference/rest/v1/documents/get
# Example `arcade chat` query: `get document with ID 1234567890`
# Note: Document IDs are returned in the response of the Google Drive's `list_documents` tool
@tool(
    requires_auth=Google(
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
        ],
    ),
)
async def get_document_by_id(
    context: ToolContext,
    document_id: Annotated[str, "The ID of the document to retrieve."],
) -> Annotated[dict, "The document contents as a dictionary"]:
    """
    DEPRECATED DO NOT USE THIS TOOL
    Get the latest version of the specified Google Docs document.
    """
    service = build_docs_service(context.get_auth_token_or_empty())

    # Execute the documents().get() method. Returns a Document object
    # https://developers.google.com/docs/api/reference/rest/v1/documents#Document
    request = service.documents().get(documentId=document_id)
    response = request.execute()
    return dict(response)


@tool(
    requires_auth=Google(
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
        ],
    ),
)
async def get_document_as_docmd(
    context: ToolContext,
    document_id: Annotated[str, "The ID of the document to retrieve."],
) -> Annotated[str, "The document contents as DocMD"]:
    """
    Get the latest version of the specified Google Docs document as DocMD.
    The DocMD output will include tags that can be used to annotate the document with location
    information, the type of block, block IDs, and other metadata.
    """
    service = build_docs_service(context.get_auth_token_or_empty())

    request = service.documents().get(documentId=document_id)
    response = request.execute()
    return build_docmd(Document(**response)).to_string()
