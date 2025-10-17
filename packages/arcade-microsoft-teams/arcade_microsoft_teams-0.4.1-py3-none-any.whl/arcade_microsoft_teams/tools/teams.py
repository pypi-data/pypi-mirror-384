from typing import Annotated, cast

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Microsoft
from arcade_tdk.errors import ToolExecutionError

from arcade_microsoft_teams.client import get_client
from arcade_microsoft_teams.constants import TeamMembershipType
from arcade_microsoft_teams.serializers import (
    serialize_associated_team,
    serialize_member,
    serialize_team,
)
from arcade_microsoft_teams.utils import (
    build_offset_pagination,
    build_startswith_filter_clause,
    build_token_pagination,
    find_unique_team_by_name,
    find_unique_user_team,
    members_request,
    teams_request,
)


@tool(requires_auth=Microsoft(scopes=["Team.ReadBasic.All"]))
async def list_teams(
    context: ToolContext,
    membership_type: Annotated[
        TeamMembershipType,
        "The type of membership to filter by. Defaults to 'direct_member_of_the_team'.",
    ] = TeamMembershipType.DIRECT_MEMBER,
) -> Annotated[
    dict,
    "The teams the current user is associated with.",
]:
    """Lists the teams the current user is associated with in Microsoft Teams."""
    client = get_client(context.get_auth_token_or_empty())

    if membership_type == TeamMembershipType.DIRECT_MEMBER:
        response = await client.me.joined_teams.get()
        if not response or not isinstance(response.value, list):
            return {"teams": []}
        return {"teams": [serialize_team(team) for team in response.value]}

    elif membership_type == TeamMembershipType.MEMBER_OF_SHARED_CHANNEL:
        response_associated = await client.me.teamwork.associated_teams.get()
        if not response_associated or not isinstance(response_associated.value, list):
            return {"teams": []}
        return {"teams": [serialize_associated_team(team) for team in response_associated.value]}


@tool(requires_auth=Microsoft(scopes=["Team.ReadBasic.All"]))
async def search_teams(
    context: ToolContext,
    team_name_starts_with: Annotated[
        str,
        "The prefix to match the name of the teams.",
    ],
    limit: Annotated[
        int,
        "The maximum number of teams to return. Defaults to 10, max is 50.",
    ] = 10,
    next_page_token: Annotated[
        str | None,
        "The token to use to get the next page of results.",
    ] = None,
) -> Annotated[
    dict,
    "Search for teams in the organization (regardless of whether the current user is a member).",
]:
    """Searches for teams available to the current user in Microsoft Teams."""
    limit = min(50, max(1, limit))
    client = get_client(context.get_auth_token_or_empty())

    filter_by_name = build_startswith_filter_clause(
        field="displayName",
        starts_with=team_name_starts_with,
        use_case_variants=True,
    )

    response = await client.teams.get(
        teams_request(
            top=limit,
            filter_=filter_by_name,
            skiptoken=next_page_token,
        )
    )

    if not response or not isinstance(response.value, list):
        return {
            "teams": [],
            "count": 0,
            "pagination": {},
        }

    return {
        "teams": [serialize_team(team) for team in response.value],
        "pagination": build_token_pagination(response),
    }


@tool(requires_auth=Microsoft(scopes=["Team.ReadBasic.All"]))
async def get_team(
    context: ToolContext,
    team_id: Annotated[str | None, "The ID of the team to get."] = None,
    team_name: Annotated[
        str | None,
        "The name of the team to get. Prefer providing a team_id, when available, for optimal "
        "performance.",
    ] = None,
) -> Annotated[dict, "The team metadata."]:
    """Retrieves metadata about a team in Microsoft Teams.

    Provide one of team_id OR team_name, never both. When available, prefer providing a team_id for
    optimal performance.

    If team_id nor team_name are provided: 1) if the user has a single team, the tool will retrieve
    it; 2) if the user has multiple teams, an error will be returned with a list of all teams to
    pick from.
    """
    client = get_client(context.get_auth_token_or_empty())

    if team_id and team_name:
        message = "Provide one of team_id or team_name."
        raise ToolExecutionError(message=message, developer_message=message)

    if not team_id and not team_name:
        response = await find_unique_user_team(context)
        team_id = response["id"]

    if team_id:
        response_team = await client.teams.by_team_id(team_id).get()
        if not response_team:
            raise ToolExecutionError(
                message="Team not found",
                developer_message=f"Team with ID '{team_id}' not found",
            )
        return serialize_team(response_team)

    return await find_unique_team_by_name(context, cast(str, team_name))


@tool(requires_auth=Microsoft(scopes=["TeamMember.Read.All"]))
async def list_team_members(
    context: ToolContext,
    team_id: Annotated[
        str | None,
        "The ID of the team to list the members of.",
    ] = None,
    team_name: Annotated[
        str | None,
        "The name of the team to list the members of. Prefer providing a team_id, when available, "
        "for optimal performance.",
    ] = None,
    limit: Annotated[
        int,
        "The maximum number of members to return. Defaults to 50, max is 999.",
    ] = 50,
    offset: Annotated[int, "The number of members to skip. Defaults to 0."] = 0,
) -> Annotated[
    dict,
    "The members of the team.",
]:
    """Lists the members of a team in Microsoft Teams.

    Provide one of team_id OR team_name, never both. When available, prefer providing a team_id for
    optimal performance.

    If team_id nor team_name are provided: 1) if the user has a single team, the tool will use it;
    2) if the user has multiple teams, an error will be returned with a list of all teams to pick
    from.

    The Microsoft Graph API returns only up to the first 999 members.
    """
    limit = min(999, max(1, limit))

    if limit + offset > 999:
        offset = 999 - limit

    if team_id and team_name:
        message = "Provide one of team_id or team_name."
        raise ToolExecutionError(message=message, developer_message=message)

    if not team_id and not team_name:
        response = await find_unique_user_team(context)
        team_id = response["id"]
        team_name = response["name"]

    if team_name:
        response = await find_unique_team_by_name(context, team_name)
        team_id = response["id"]

    client = get_client(context.get_auth_token_or_empty())
    response_members = await client.teams.by_team_id(cast(str, team_id)).members.get(
        members_request(top=limit)
    )

    if not response_members or not isinstance(response_members.value, list):
        return {
            "members": [],
            "count": 0,
            "team": {"id": team_id, "name": team_name},
        }

    members = [
        serialize_member(member) for member in response_members.value[offset : offset + limit]
    ]

    return {
        "members": members,
        "count": len(members),
        "team": {"id": team_id, "name": team_name},
        "pagination": build_offset_pagination(members, limit, offset),
    }


@tool(requires_auth=Microsoft(scopes=["TeamMember.Read.All"]))
async def search_team_members(
    context: ToolContext,
    member_name_starts_with: Annotated[
        str,
        "The prefix to match the name of the members.",
    ],
    team_id: Annotated[
        str | None,
        "The ID of the team to list the members of.",
    ] = None,
    team_name: Annotated[
        str | None,
        "The name of the team to list the members of. Prefer providing a team_id, when available, "
        "for optimal performance.",
    ] = None,
    limit: Annotated[
        int,
        "The maximum number of members to return. Defaults to 50, max is 100.",
    ] = 50,
    offset: Annotated[int, "The number of members to skip. Defaults to 0."] = 0,
) -> Annotated[
    dict,
    "The members of the team.",
]:
    """Searches for members of a team in Microsoft Teams.

    Provide one of team_id OR team_name, never both. When available, prefer providing a team_id for
    optimal performance.

    If team_id nor team_name are provided: 1) if the user has a single team, the tool will use it;
    2) if the user has multiple teams, an error will be raised with a list of available teams to
    pick from.

    The Microsoft Graph API returns only up to the first 999 members of a team.
    """
    limit = min(100, max(1, limit))

    if team_id and team_name:
        message = "Provide one of team_id or team_name."
        raise ToolExecutionError(message=message, developer_message=message)

    if not team_id and not team_name:
        response = await find_unique_user_team(context)
        team_id = response["id"]
        team_name = response["name"]

    if team_name:
        response = await find_unique_team_by_name(context, cast(str, team_name))
        team_id = response["id"]

    filter_by_name = build_startswith_filter_clause(
        field="displayName",
        starts_with=member_name_starts_with,
        use_case_variants=True,
    )

    client = get_client(context.get_auth_token_or_empty())
    response_members = await client.teams.by_team_id(cast(str, team_id)).members.get(
        members_request(top=limit, filter_=filter_by_name)
    )

    if not response_members or not isinstance(response_members.value, list):
        return {
            "members": [],
            "count": 0,
            "team": {"id": team_id, "name": team_name},
        }

    members = [
        serialize_member(member) for member in response_members.value[offset : offset + limit]
    ]

    return {
        "members": members,
        "count": len(members),
        "team": {"id": team_id, "name": team_name},
        "pagination": build_offset_pagination(members, limit, offset),
    }
