from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Google

from arcade_google_calendar.utils import build_calendar_service, build_oauth_service
from arcade_google_calendar.who_am_i_util import build_who_am_i_response


@tool(
    requires_auth=Google(
        scopes=[
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ]
    )
)
async def who_am_i(
    context: ToolContext,
) -> Annotated[
    dict[str, Any],
    "Get comprehensive user profile and Google Calendar environment information.",
]:
    """
    Get comprehensive user profile and Google Calendar environment information.

    This tool provides detailed information about the authenticated user including
    their name, email, profile picture, Google Calendar access permissions, and other
    important profile details from Google services.
    """

    calendar_service = build_calendar_service(context.get_auth_token_or_empty())
    oauth_service = build_oauth_service(context.get_auth_token_or_empty())
    user_info = build_who_am_i_response(context, calendar_service, oauth_service)

    return dict(user_info)
