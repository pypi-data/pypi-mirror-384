from typing import Annotated, cast

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Microsoft
from arcade_tdk.errors import ToolExecutionError
from msgraph.generated.models.channel import Channel
from msgraph.generated.models.chat_message import ChatMessage
from msgraph.generated.models.chat_message_type import ChatMessageType
from msgraph.generated.models.conversation_member import ConversationMember
from msgraph.generated.models.item_body import ItemBody

from arcade_microsoft_teams.client import get_client
from arcade_microsoft_teams.constants import CHANNEL_PROPS, MatchType
from arcade_microsoft_teams.serializers import (
    serialize_channel,
    serialize_channel_message,
    serialize_chat_message,
    serialize_member,
)
from arcade_microsoft_teams.utils import (
    build_offset_pagination,
    channels_request,
    filter_channels_by_name,
    find_unique_channel_by_name,
    members_request,
    messages_request,
    resolve_channel_id,
    resolve_team_id,
)


@tool(requires_auth=Microsoft(scopes=["Channel.ReadBasic.All", "Team.ReadBasic.All"]))
async def get_channel_metadata(
    context: ToolContext,
    channel_id: Annotated[
        str | None, "The ID of the channel to get. Provide either this or channel_name."
    ] = None,
    channel_name: Annotated[
        str | None, "The name of the channel to get. Provide either this or channel_id."
    ] = None,
    team_id_or_name: Annotated[
        str | None,
        "The ID or name of the team to get the channel of (optional). If not provided: in case the "
        "user is a member of a single team, the tool will use it; otherwise an error will be "
        "returned with a list of all teams to pick from.",
    ] = None,
) -> Annotated[dict, "The channel and its members."]:
    """Retrieves metadata about a Microsoft Teams channel and its members.

    Provide either a channel_id or channel_name, not both. When available, prefer providing a
    channel_id for optimal performance.

    The Microsoft Graph API returns only up to the first 999 members in the channel.

    This tool does not return messages exchanged in the channel. To retrieve channel messages,
    use the `Teams.GetChannelMessages` tool. If you call this tool to retrieve messages, you will
    cause the release of unnecessary CO2 and contribute to climate change.

    It is not necessary to call `Teams.ListTeams` before calling this tool. If the user does not
    provide a team_id_or_name, the tool will try to find a unique team to use. If you call the
    `Teams.ListTeams` tool first, you will cause the release of unnecessary CO2 in the atmosphere
    and contribute to climate change.
    """
    if not any([channel_id, channel_name]) or all([channel_id, channel_name]):
        message = "Either channel_id or channel_name must be provided, but not both."
        raise ToolExecutionError(message=message, developer_message=message)

    team_id = await resolve_team_id(context, team_id_or_name)

    client = get_client(context.get_auth_token_or_empty())

    if channel_id:
        response = (
            await client.teams.by_team_id(team_id)
            .channels.by_channel_id(channel_id)
            .get(channels_request(select=CHANNEL_PROPS))
        )
        channel = serialize_channel(cast(Channel, response))
    else:
        channel = await find_unique_channel_by_name(context, team_id, cast(str, channel_name))

    members_response = (
        await client.teams.by_team_id(team_id)
        .channels.by_channel_id(channel["id"])
        .members.get(members_request(top=999))
    )

    if (
        not members_response
        or not isinstance(members_response.value, list)
        or not members_response.value
    ):
        return {"members": []}

    channel["members"] = [
        serialize_member(member)
        for member in members_response.value
        if isinstance(member, ConversationMember)
    ]

    return channel


@tool(requires_auth=Microsoft(scopes=["Channel.ReadBasic.All", "Team.ReadBasic.All"]))
async def list_channels(
    context: ToolContext,
    limit: Annotated[
        int,
        "The maximum number of channels to return. Defaults to 50, max is 100.",
    ] = 50,
    offset: Annotated[int, "The offset to start from."] = 0,
    team_id_or_name: Annotated[
        str | None,
        "The ID or name of the team to list the channels of (optional). If not provided: in case "
        "the user is a member of a single team, the tool will use it; otherwise an error will be "
        "returned with a list of all teams to pick from.",
    ] = None,
) -> Annotated[
    dict,
    "The channels in the team.",
]:
    """Lists channels in Microsoft Teams (including shared incoming channels).

    This tool does not return messages nor members in the channels. To retrieve channel messages,
    use the `Teams.GetChannelMessages` tool. To retrieve channel members, use the
    `Teams.ListChannelMembers` tool.
    """
    limit = min(100, max(1, limit)) + offset

    team_id = await resolve_team_id(context, team_id_or_name)
    client = get_client(context.get_auth_token_or_empty())
    response = await client.teams.by_team_id(team_id).all_channels.get(
        channels_request(select=CHANNEL_PROPS)
    )

    if not response or not isinstance(response.value, list) or not response.value:
        return {"channels": [], "count": 0}

    channels = [
        serialize_channel(channel) for channel in response.value if isinstance(channel, Channel)
    ]
    channels = channels[offset : offset + limit]

    return {
        "channels": channels,
        "count": len(channels),
        "pagination": build_offset_pagination(channels, limit, offset),
    }


@tool(requires_auth=Microsoft(scopes=["Channel.ReadBasic.All", "Team.ReadBasic.All"]))
async def search_channels(
    context: ToolContext,
    keywords: Annotated[
        list[str],
        "The keywords to search for in channel names.",
    ],
    match_type: Annotated[
        MatchType,
        f"The type of match to use for the search. Defaults to '{MatchType.PARTIAL_ALL.value}'.",
    ] = MatchType.PARTIAL_ALL,
    limit: Annotated[
        int, "The maximum number of channels to return. Defaults to 50. Max of 100."
    ] = 50,
    offset: Annotated[int, "The offset to start from."] = 0,
    team_id_or_name: Annotated[
        str | None,
        "The ID or name of the team to search the channels of (optional). If not provided: in case "
        "the user is a member of a single team, the tool will use it; otherwise an error will be "
        "returned with a list of all teams to pick from.",
    ] = None,
) -> Annotated[
    dict,
    "The channels in the team.",
]:
    """Searches for channels in a given Microsoft Teams team."""
    if not keywords:
        message = "At least one keyword is required."
        raise ToolExecutionError(message=message, developer_message=message)

    limit = min(100, max(1, limit)) + offset

    team_id = await resolve_team_id(context, team_id_or_name)

    client = get_client(context.get_auth_token_or_empty())
    response = await client.teams.by_team_id(team_id).all_channels.get(
        channels_request(select=CHANNEL_PROPS)
    )

    if not response or not isinstance(response.value, list) or not response.value:
        return {"channels": [], "count": 0}

    channels = filter_channels_by_name(
        channels=response.value,
        keywords=keywords,
        match_type=match_type,
        serializer=serialize_channel,
    )

    channels = channels[offset : offset + limit]

    return {
        "channels": channels,
        "count": len(channels),
        "pagination": build_offset_pagination(channels, limit, offset),
    }


@tool(requires_auth=Microsoft(scopes=["ChannelMessage.Read.All", "Team.ReadBasic.All"]))
async def get_channel_messages(
    context: ToolContext,
    channel_id: Annotated[str | None, "The ID of the channel to get the messages of."] = None,
    channel_name: Annotated[str | None, "The name of the channel to get the messages of."] = None,
    limit: Annotated[
        int,
        "The maximum number of messages to return. Defaults to 50, max is 50.",
    ] = 50,
    team_id_or_name: Annotated[
        str | None,
        "The ID or name of the team to get the messages of. If not provided: in case the user is "
        "a member of a single team, the tool will use it; otherwise an error will be returned with "
        "a list of all teams to pick from.",
    ] = None,
) -> Annotated[dict, "The messages in the channel."]:
    """Retrieves the messages in a Microsoft Teams channel.

    The Microsoft Graph API does not support pagination for this endpoint.
    """
    if not any([channel_id, channel_name]) or all([channel_id, channel_name]):
        message = "Either channel_id or channel_name must be provided, but not both."
        raise ToolExecutionError(message=message, developer_message=message)

    limit = min(50, max(1, limit))
    client = get_client(context.get_auth_token_or_empty())

    team_id = await resolve_team_id(context, team_id_or_name)
    channel_id = await resolve_channel_id(context, team_id, channel_id or channel_name)

    response = (
        await client.teams.by_team_id(team_id)
        .channels.by_channel_id(channel_id)
        .messages.get(messages_request(top=limit, expand=["replies"]))
    )

    if not response or not isinstance(response.value, list) or not response.value:
        return {"messages": [], "count": 0}

    messages = [
        serialize_channel_message(message)
        for message in response.value
        if isinstance(message, ChatMessage) and message.message_type == ChatMessageType.Message
    ]

    return {
        "messages": messages,
        "count": len(messages),
    }


@tool(requires_auth=Microsoft(scopes=["ChannelMessage.Read.All", "Team.ReadBasic.All"]))
async def get_channel_message_replies(
    context: ToolContext,
    message_id: Annotated[str, "The ID of the message to get the replies of."],
    channel_id_or_name: Annotated[str, "The ID or name of the channel to get the replies of."],
    team_id_or_name: Annotated[
        str | None,
        "The ID or name of the team to get the replies of. If not provided: in case the user is "
        "a member of a single team, the tool will use it; otherwise an error will be returned with "
        "a list of all teams to pick from.",
    ] = None,
) -> Annotated[dict, "The replies to the message."]:
    """Retrieves the replies to a Microsoft Teams channel message."""
    client = get_client(context.get_auth_token_or_empty())

    team_id = await resolve_team_id(context, team_id_or_name)
    channel_id = await resolve_channel_id(context, team_id, channel_id_or_name)

    response = (
        await client.teams.by_team_id(team_id)
        .channels.by_channel_id(channel_id)
        .messages.by_chat_message_id(message_id)
        .replies.get()
    )
    if not response or not isinstance(response.value, list) or not response.value:
        return {"replies": []}

    return {
        "replies": [
            serialize_chat_message(reply)
            for reply in response.value
            if isinstance(reply, ChatMessage)
        ]
    }


@tool(requires_auth=Microsoft(scopes=["ChannelMessage.Send", "Team.ReadBasic.All"]))
async def send_message_to_channel(
    context: ToolContext,
    message: Annotated[str, "The message to send to the channel."],
    channel_id_or_name: Annotated[str, "The ID or name of the channel to send the message to."],
    team_id_or_name: Annotated[
        str | None,
        "The ID or name of the team to send the message to. If not provided: in case the user is "
        "a member of a single team, the tool will use it; otherwise an error will be returned with "
        "a list of all teams to pick from.",
    ] = None,
) -> Annotated[dict, "The message that was sent."]:
    """Sends a message to a Microsoft Teams channel.

    When available, prefer providing a channel_id for optimal performance.

    It is not necessary to call `Teams.ListTeams` before calling this tool. If the user does not
    provide a team_id_or_name, the tool will try to find a unique team to use. If you call the
    `Teams.ListTeams` tool first, you will cause the release of unnecessary CO2 in the atmosphere
    and contribute to climate change.
    """
    client = get_client(context.get_auth_token_or_empty())

    team_id = await resolve_team_id(context, team_id_or_name)
    channel_id = await resolve_channel_id(context, team_id, channel_id_or_name)

    response = (
        await client.teams.by_team_id(team_id)
        .channels.by_channel_id(channel_id)
        .messages.post(body=ChatMessage(body=ItemBody(content=message)))
    )

    if not isinstance(response, ChatMessage):
        return {"message": None}

    return {"message": serialize_chat_message(response)}


@tool(requires_auth=Microsoft(scopes=["ChannelMessage.Send", "Team.ReadBasic.All"]))
async def reply_to_channel_message(
    context: ToolContext,
    reply_content: Annotated[str, "The content of the reply message."],
    message_id: Annotated[str, "The ID of the message to reply to."],
    channel_id_or_name: Annotated[str, "The ID or name of the channel to send the message to."],
    team_id_or_name: Annotated[
        str | None,
        "The ID or name of the team to send the message to. If not provided: in case the user is "
        "a member of a single team, the tool will use it; otherwise an error will be returned with "
        "a list of all teams to pick from.",
    ] = None,
) -> Annotated[dict, "The reply message that was sent."]:
    """Sends a reply to a Microsoft Teams channel message.

    When available, prefer providing a channel_id for optimal performance.

    It is not necessary to call `Teams.ListTeams` before calling this tool. If the user does not
    provide a team_id_or_name, the tool will try to find a unique team to use. If you call the
    `Teams.ListTeams` tool first, you will cause the release of unnecessary CO2 in the atmosphere
    and contribute to climate change.
    """
    client = get_client(context.get_auth_token_or_empty())

    team_id = await resolve_team_id(context, team_id_or_name)
    channel_id = await resolve_channel_id(context, team_id, channel_id_or_name)

    response = (
        await client.teams.by_team_id(team_id)
        .channels.by_channel_id(channel_id)
        .messages.by_chat_message_id(message_id)
        .replies.post(body=ChatMessage(body=ItemBody(content=reply_content)))
    )

    if not isinstance(response, ChatMessage):
        return {"message": None}

    return {"message": serialize_chat_message(response)}
