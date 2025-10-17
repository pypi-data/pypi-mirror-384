"""Utilities for Microsoft Graph API filtering operations."""

import asyncio

from arcade_tdk import ToolContext
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.models.chat import Chat
from msgraph.generated.models.chat_collection_response import ChatCollectionResponse
from msgraph.generated.users.item.chats.chats_request_builder import ChatsRequestBuilder

from arcade_microsoft_teams.client import get_client


async def filter_chats_by_member_display_names_exact(
    context: ToolContext,
    display_names: list[str],
    semaphore: asyncio.Semaphore | None = None,
) -> list[Chat]:
    """Filter chats that contain exactly the specified members."""
    if not display_names:
        return []

    filter_string = _build_member_filter_query_by_display_name(display_names)

    chats = await filter_chats_with_odata_filter(
        context=context,
        filter_string=filter_string,
        semaphore=semaphore,
    )

    exact_match_chats = []
    display_names_set = set(display_names)

    for chat in chats:
        if chat.members:
            chat_display_names = set()
            for member in chat.members:
                if hasattr(member, "display_name") and member.display_name:
                    chat_display_names.add(member.display_name)

            if chat_display_names == display_names_set:
                exact_match_chats.append(chat)

    return exact_match_chats


async def filter_chats_with_odata_filter(
    context: ToolContext,
    filter_string: str,
    semaphore: asyncio.Semaphore | None = None,
) -> list[Chat]:
    """Filter chats using Microsoft Graph API OData filters."""
    query_params = ChatsRequestBuilder.ChatsRequestBuilderGetQueryParameters(
        expand=["members"],
        filter=filter_string,
        orderby=["lastMessagePreview/createdDateTime desc"],
        top=50,
    )

    request_configuration = RequestConfiguration(query_parameters=query_params)
    client = get_client(context.get_auth_token_or_empty())

    if semaphore:
        async with semaphore:
            response = await client.me.chats.get(request_configuration=request_configuration)
    else:
        response = await client.me.chats.get(request_configuration=request_configuration)

    if not isinstance(response, ChatCollectionResponse) or not response.value:
        return []

    return response.value


def _build_member_filter_query_by_display_name(display_names: list[str]) -> str:
    """Build a filter query string for chat members using display names."""
    filter_clauses = []
    for i, display_name in enumerate(display_names):
        escaped_name = display_name.replace("'", "''")
        filter_clauses.append(f"members/any(m{i}:m{i}/displayName eq '{escaped_name}')")

    return " and ".join(filter_clauses)
