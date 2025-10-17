from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Google

from arcade_google_contacts.utils import build_people_service
from arcade_google_contacts.who_am_i_util import build_who_am_i_response


@tool(
    requires_auth=Google(
        scopes=[
            "https://www.googleapis.com/auth/contacts.readonly",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ]
    )
)
async def who_am_i(
    context: ToolContext,
) -> Annotated[
    dict[str, Any],
    "Get comprehensive user profile and Google Contacts environment information.",
]:
    """
    Get comprehensive user profile and Google Contacts environment information.

    This tool provides detailed information about the authenticated user including
    their name, email, profile picture, Google Contacts access permissions, and other
    important profile details from Google services.
    """

    people_service = build_people_service(context.get_auth_token_or_empty())
    user_info = build_who_am_i_response(context, people_service)

    return dict(user_info)
