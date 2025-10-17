from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Microsoft

from arcade_outlook_calendar.client import get_client
from arcade_outlook_calendar.who_am_i_util import build_who_am_i_response


@tool(
    requires_auth=Microsoft(
        scopes=[
            "User.Read",
            "Calendars.ReadBasic",
        ]
    )
)
async def who_am_i(
    context: ToolContext,
) -> Annotated[
    dict[str, Any],
    "Get comprehensive user profile and Outlook Calendar information.",
]:
    """
    Get information about the current user and their Outlook Calendar environment.
    """
    client = get_client(context.get_auth_token_or_empty())
    user_info = await build_who_am_i_response(client)
    return dict(user_info)
