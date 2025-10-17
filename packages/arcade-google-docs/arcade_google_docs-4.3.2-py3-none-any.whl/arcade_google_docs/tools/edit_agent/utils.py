from typing import Any

from arcade_google_docs.docmd import DocMD, build_docmd
from arcade_google_docs.models.document import Document


def get_docmd(google_service: Any, document_id: str) -> DocMD:
    """
    Helper function to get a Google Doc and convert it to DocMD format.

    Args:
        google_service: The authenticated Google Docs service
        document_id: The ID of the document to fetch

    Returns:
        DocMD object
    """
    google_get_response = google_service.documents().get(documentId=document_id).execute()
    document = Document(**google_get_response)
    docmd = build_docmd(document)
    return docmd
