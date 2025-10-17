from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Microsoft

from arcade_microsoft_teams.client import get_client
from arcade_microsoft_teams.who_am_i_util import build_who_am_i_response


@tool(
    requires_auth=Microsoft(
        scopes=[
            "User.Read",
        ]
    )
)
async def who_am_i(
    context: ToolContext,
) -> Annotated[
    dict[str, Any],
    "Get comprehensive user profile and Microsoft Teams information.",
]:
    """
    Get information about the current user and their Microsoft Teams environment.
    """
    client = get_client(context.get_auth_token_or_empty())
    user_info = await build_who_am_i_response(client)
    return dict(user_info)
