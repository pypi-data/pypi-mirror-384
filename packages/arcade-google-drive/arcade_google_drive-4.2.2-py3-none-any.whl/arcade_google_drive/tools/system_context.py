from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Google

from arcade_google_drive.utils import build_drive_service
from arcade_google_drive.who_am_i_util import build_who_am_i_response


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
    "Get comprehensive user profile and Google Drive environment information.",
]:
    """
    Get comprehensive user profile and Google Drive environment information.

    This tool provides detailed information about the authenticated user including
    their name, email, profile picture, Google Drive storage information, and other
    important profile details from Google services.
    """

    drive_service = build_drive_service(context.get_auth_token_or_empty())
    user_info = build_who_am_i_response(context, drive_service)

    return dict(user_info)
