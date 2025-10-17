import logging
from typing import Any, cast

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from arcade_google_slides.converters import PresentationMarkdownConverter
from arcade_google_slides.enum import Corpora, OrderBy
from arcade_google_slides.types import Presentation

## Set up basic configuration for logging to the console with DEBUG level and a specific format.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def build_slides_service(auth_token: str | None) -> Resource:  # type: ignore[no-any-unimported]
    """
    Build a Slides service object.
    """
    auth_token = auth_token or ""
    return build("slides", "v1", credentials=Credentials(auth_token))


def build_drive_service(auth_token: str | None) -> Resource:  # type: ignore[no-any-unimported]
    """
    Build a Drive service object.
    """
    auth_token = auth_token or ""
    return build("drive", "v3", credentials=Credentials(auth_token))


def create_blank_presentation(  # type: ignore[no-any-unimported]
    slides_service: Resource,
    title: str,
) -> Presentation:
    """
    Create a blank Google Slides presentation with the specified title.

    Requires the https://www.googleapis.com/auth/drive.file scope

    Args:
        slides_service: The Slides service to use
        title: The title of the presentation to create

    Returns:
        The created presentation
    """
    blank_presentation: Presentation = {
        "title": title,
        "presentationId": None,
        "slides": [],
    }

    request = slides_service.presentations().create(body=blank_presentation)
    response = request.execute()

    return cast(Presentation, response)


def convert_presentation_to_markdown(presentation: Presentation) -> str:
    """
    Convert a Google Slides presentation to markdown format.

    This function uses the PresentationMarkdownConverter class to perform
    the conversion following the strict TypedDict structure.

    Args:
        presentation: Presentation TypedDict

    Returns:
        A markdown string representation of the presentation
    """
    converter = PresentationMarkdownConverter()
    return converter.convert(presentation)


def build_files_list_params(
    mime_type: str,
    page_size: int,
    order_by: list[OrderBy] | None,
    pagination_token: str | None,
    include_shared_drives: bool,
    search_only_in_shared_drive_id: str | None,
    include_organization_domain_documents: bool,
    document_contains: list[str] | None = None,
    document_not_contains: list[str] | None = None,
) -> dict[str, Any]:
    query = build_files_list_query(
        mime_type=mime_type,
        document_contains=document_contains,
        document_not_contains=document_not_contains,
    )

    params = {
        "q": query,
        "pageSize": page_size,
        "orderBy": ",".join([item.value for item in order_by]) if order_by else None,
        "pageToken": pagination_token,
    }

    if (
        include_shared_drives
        or search_only_in_shared_drive_id
        or include_organization_domain_documents
    ):
        params["includeItemsFromAllDrives"] = "true"
        params["supportsAllDrives"] = "true"

    if search_only_in_shared_drive_id:
        params["driveId"] = search_only_in_shared_drive_id
        params["corpora"] = Corpora.DRIVE.value

    if include_organization_domain_documents:
        params["corpora"] = Corpora.DOMAIN.value

    params = remove_none_values(params)

    return params


def build_files_list_query(
    mime_type: str,
    document_contains: list[str] | None = None,
    document_not_contains: list[str] | None = None,
) -> str:
    query = [f"(mimeType = '{mime_type}' and trashed = false)"]

    if isinstance(document_contains, str):
        document_contains = [document_contains]

    if isinstance(document_not_contains, str):
        document_not_contains = [document_not_contains]

    if document_contains:
        for keyword in document_contains:
            name_contains = keyword.replace("'", "\\'")
            full_text_contains = keyword.replace("'", "\\'")
            keyword_query = (
                f"(name contains '{name_contains}' or fullText contains '{full_text_contains}')"
            )
            query.append(keyword_query)

    if document_not_contains:
        for keyword in document_not_contains:
            name_not_contains = keyword.replace("'", "\\'")
            full_text_not_contains = keyword.replace("'", "\\'")
            keyword_query = (
                f"(not (name contains '{name_not_contains}' or "
                f"fullText contains '{full_text_not_contains}'))"
            )
            query.append(keyword_query)

    return " and ".join(query)


def remove_none_values(params: dict) -> dict:
    """
    Remove None values from a dictionary.
    :param params: The dictionary to clean
    :return: A new dictionary with None values removed
    """
    return {k: v for k, v in params.items() if v is not None}
