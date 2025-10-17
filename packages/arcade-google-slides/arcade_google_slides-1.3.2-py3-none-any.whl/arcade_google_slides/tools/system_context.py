from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Google

from arcade_google_slides.utils import build_slides_service
from arcade_google_slides.who_am_i_util import build_who_am_i_response


@tool(
    requires_auth=Google(
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ]
    )
)
async def who_am_i(
    context: ToolContext,
) -> Annotated[
    dict[str, Any],
    "Get comprehensive user profile and Google Slides environment information.",
]:
    """
    Get comprehensive user profile and Google Slides environment information.

    This tool provides detailed information about the authenticated user including
    their name, email, profile picture, Google Slides access permissions, and other
    important profile details from Google services.
    """

    auth_token = context.get_auth_token_or_empty()
    slides_service = build_slides_service(auth_token)
    user_info = build_who_am_i_response(context, slides_service)

    return dict(user_info)
