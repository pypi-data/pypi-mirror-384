from typing import Annotated

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Microsoft
from arcade_tdk.errors import ToolExecutionError

from arcade_microsoft_teams.client import get_client
from arcade_microsoft_teams.constants import PartialMatchType
from arcade_microsoft_teams.serializers import serialize_person
from arcade_microsoft_teams.utils import (
    build_people_search_clause,
    build_token_pagination,
    people_request,
)


@tool(requires_auth=Microsoft(scopes=["People.Read"]))
async def search_people(
    context: ToolContext,
    keywords: Annotated[
        list[str],
        "The keywords to match against people's names. Provide one or more expressions.",
    ],
    match_type: Annotated[
        PartialMatchType,
        "The type of match to use for the keywords. "
        f"Defaults to {PartialMatchType.PARTIAL_ANY.value}.",
    ] = PartialMatchType.PARTIAL_ANY,
    limit: Annotated[
        int, "The maximum number of people to return. Defaults to 50, max is 100."
    ] = 50,
    next_page_token: Annotated[str | None, "The next page token to use for pagination."] = None,
) -> Annotated[dict, "The people matching the search criteria."]:
    """Searches for people the user has interacted with in Microsoft Teams and other 365 products.

    This tool only returns users that the currently signed in user has interacted with. It may also
    include people that are part of external tenants/organizations. If you need to retrieve users
    that may not have interacted with the current user and/or that are exclusively part of the same
    tenant, use the `Teams.SearchUsers` tool instead.
    """
    limit = min(100, max(1, limit))

    if not keywords:
        error = "At least one keyword is required."
        raise ToolExecutionError(message=error, developer_message=error)

    client = get_client(context.get_auth_token_or_empty())
    response = await client.me.people.get(
        people_request(
            top=limit,
            search=build_people_search_clause(keywords, match_type),
            next_page_token=next_page_token,
        ),
    )

    if not response or not isinstance(response.value, list):
        return {
            "people": [],
            "count": 0,
            "pagination": {},
        }

    people = [serialize_person(person) for person in response.value]

    return {
        "people": people,
        "count": len(people),
        "pagination": build_token_pagination(response),
    }
