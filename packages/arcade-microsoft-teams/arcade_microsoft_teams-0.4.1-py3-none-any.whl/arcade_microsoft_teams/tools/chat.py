import json
from typing import Annotated, cast

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Microsoft
from arcade_tdk.errors import ToolExecutionError
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.chat import Chat
from msgraph.generated.models.chat_collection_response import ChatCollectionResponse
from msgraph.generated.models.chat_message import ChatMessage
from msgraph.generated.models.chat_message_attachment import ChatMessageAttachment
from msgraph.generated.models.chat_message_type import ChatMessageType
from msgraph.generated.models.item_body import ItemBody

from arcade_microsoft_teams.client import get_client
from arcade_microsoft_teams.constants import DatetimeField
from arcade_microsoft_teams.serializers import serialize_chat, serialize_chat_message
from arcade_microsoft_teams.utils import (
    add_current_user_id,
    build_conversation_member,
    build_reply_body_from_original_message,
    build_token_pagination,
    chats_request,
    create_chat_request,
    find_chat_by_users,
    find_humans_by_name,
    messages_request,
    populate_message_for_reply,
    validate_datetime_range,
)


@tool(requires_auth=Microsoft(scopes=["Chat.Read"]))
async def get_chat_message_by_id(
    context: ToolContext,
    message_id: Annotated[str, "The ID of the message to get."],
    chat_id: Annotated[str, "The ID of the chat to get the message from."],
    user_ids: Annotated[
        list[str] | None, "The IDs of the users in the chat to get the message from."
    ] = None,
    user_names: Annotated[
        list[str] | None,
        "The names of the users in the chat to get the message from. Prefer providing user_ids, "
        "when available, since the performance is better.",
    ] = None,
) -> Annotated[dict, "The message."]:
    """Retrieves a Microsoft Teams chat message."""
    client = get_client(context.get_auth_token_or_empty())

    if chat_id and chat_id.endswith("@thread.v2"):
        message = (
            f"chat_id must be a Microsoft Teams chat ID. The value '{chat_id}' is a Channel ID."
        )
        raise ToolExecutionError(message=message, developer_message=message)

    if not chat_id:
        user_ids_with_current_user = await add_current_user_id(context, user_ids)
        chat = await find_chat_by_users(context, user_ids_with_current_user, user_names)
        chat_id = cast(str, chat["id"])

    response = (
        await client.chats.by_chat_id(cast(str, chat_id))
        .messages.by_chat_message_id(message_id)
        .get()
    )

    if not response or not isinstance(response, ChatMessage):
        return {"message": None}

    return {"message": serialize_chat_message(response)}


@tool(requires_auth=Microsoft(scopes=["Chat.Read", "Chat.Create"]))
async def get_chat_messages(
    context: ToolContext,
    chat_id: Annotated[str | None, "The ID of the chat to get messages from."] = None,
    user_ids: Annotated[
        list[str] | None, "The IDs of the users in the chat to get messages from."
    ] = None,
    user_names: Annotated[
        list[str] | None,
        "The names of the users in the chat to get messages from. Prefer providing user_ids, "
        "when available, since the performance is better.",
    ] = None,
    start_datetime: Annotated[
        str | None,
        "The start date to filter messages. Provide a string in the format 'YYYY-MM-DD' or "
        "'YYYY-MM-DD HH:MM:SS'. Defaults to None (no start date filter).",
    ] = None,
    end_datetime: Annotated[
        str | None,
        "The end date to filter messages. Provide a string in the format 'YYYY-MM-DD' or "
        "'YYYY-MM-DD HH:MM:SS'. Defaults to None (no end date filter).",
    ] = None,
    limit: Annotated[
        int,
        "The maximum number of messages to return. Defaults to 50, max is 50.",
    ] = 50,
) -> Annotated[
    dict,
    "The messages in the chat.",
]:
    """Retrieves messages from a Microsoft Teams chat (individual or group).

    Provide one of chat_id OR any combination of user_ids and/or user_names. When available, prefer
    providing a chat_id or user_ids for optimal performance.

    If the user provides user name(s), DO NOT CALL THE `Teams.SearchUsers` or `Teams.SearchPeople`
    tools first. Instead, provide the user name(s) directly to this tool through the `user_names`
    argument. It is not necessary to provide the currently signed in user's name/id, so do not call
    `Teams.GetSignedInUser` before calling this tool.

    Messages will be sorted in descending order by the messages' `created_datetime` field.

    The Microsoft Teams API does not support pagination for this tool.
    """
    if not any([chat_id, user_ids, user_names]):
        message = "At least one of chat_id, user_ids, or user_names must be provided."
        raise ToolExecutionError(message=message, developer_message=message)

    if chat_id and any([user_ids, user_names]):
        message = "chat_id and user_ids/user_names cannot be provided together."
        raise ToolExecutionError(message=message, developer_message=message)

    if chat_id and chat_id.endswith("@thread.v2"):
        from arcade_microsoft_teams.tools.channel import get_channel_messages

        message = (
            f"chat_id must be a Microsoft Teams chat ID. The value '{chat_id}' is a Channel ID. "
            f"Use the `MicrosoftTeams.{get_channel_messages.__tool_name__}` tool instead."
        )
        raise ToolExecutionError(message=message, developer_message=message)

    limit = min(50, max(1, limit))
    start_datetime, end_datetime = validate_datetime_range(start_datetime, end_datetime)

    datetime_filters = []
    datetime_field = DatetimeField.CREATED

    if start_datetime:
        datetime_filters.append(f"{datetime_field.value} ge {start_datetime}")
    if end_datetime:
        datetime_filters.append(f"{datetime_field.value} le {end_datetime}")

    filter_clause = " and ".join(datetime_filters) if datetime_filters else None

    if not chat_id:
        chat = await get_chat_metadata(
            context=context,
            user_ids=user_ids,
            user_names=user_names,
        )
        chat_id = cast(str, chat["chat"]["id"])

    client = get_client(context.get_auth_token_or_empty())
    response = await client.chats.by_chat_id(chat_id).messages.get(
        messages_request(
            top=limit,
            orderby=datetime_field.order_by_clause,
            filter=filter_clause,
        )
    )

    if not response or not isinstance(response.value, list):
        return {
            "messages": [],
            "count": 0,
            "chat": {"id": chat_id},
        }

    # Unfortunately, the MS Graph API $filter parameter does not support filtering by message type.
    # So we need to filter out non-message items, like systemEventMessage manually.
    messages = [
        serialize_chat_message(message)
        for message in response.value
        if message.message_type == ChatMessageType.Message
    ]

    return {
        "messages": messages,
        "count": len(messages),
        "chat": {"id": chat_id},
    }


@tool(requires_auth=Microsoft(scopes=["Chat.Read"]))
async def get_chat_metadata(
    context: ToolContext,
    chat_id: Annotated[str | None, "The ID of the chat to get metadata about."] = None,
    user_ids: Annotated[
        list[str] | None, "The IDs of the users in the chat to get metadata about."
    ] = None,
    user_names: Annotated[
        list[str] | None,
        "The names of the users in the chat to get messages from. Prefer providing user_ids, "
        "when available, since the performance is better.",
    ] = None,
) -> Annotated[
    dict,
    "Metadata about the chat.",
]:
    """Retrieves metadata about a Microsoft Teams chat.

    Provide exactly one of chat_id or user_ids/user_names. When available, prefer providing a
    chat_id or user_ids for optimal performance.

    If multiple roup chats exist with those exact members, returns the most recently updated one.

    Max 20 DIFFERENT users can be provided in user_ids/user_names.

    This tool DOES NOT return messages in a chat. Use the `Teams.GetChatMessages` tool to get
    chat messages.
    """
    if not any([chat_id, user_ids, user_names]):
        message = "At least one of chat_id, user_ids, or user_names must be provided."
        raise ToolExecutionError(message=message, developer_message=message)

    if chat_id and any([user_ids, user_names]):
        message = "chat_id and user_ids/user_names cannot be provided together."
        raise ToolExecutionError(message=message, developer_message=message)

    if not chat_id:
        user_ids_with_current_user = await add_current_user_id(context, user_ids)
        return await find_chat_by_users(context, user_ids_with_current_user, user_names)

    if chat_id and chat_id.endswith("@thread.v2"):
        from arcade_microsoft_teams.tools.channel import get_channel_metadata

        message = (
            f"chat_id must be a Microsoft Teams chat ID. The value '{chat_id}' is a Channel ID. "
            f"Use the `MicrosoftTeams.{get_channel_metadata.__tool_name__}` tool instead."
        )
        raise ToolExecutionError(message=message, developer_message=message)

    client = get_client(context.get_auth_token_or_empty())
    response = await client.chats.by_chat_id(chat_id).get()

    if not response or not isinstance(response, Chat):
        raise ToolExecutionError(
            message="Chat not found with id: " + chat_id,
            developer_message="Chat not found with id: " + chat_id,
        )

    return {"chat": serialize_chat(response)}


@tool(requires_auth=Microsoft(scopes=["Chat.Read"]))
async def list_chats(
    context: ToolContext,
    limit: Annotated[int, "The maximum number of chats to return. Defaults to 50, max is 50."] = 50,
    next_page_token: Annotated[
        str | None, "The token to use to get the next page of results."
    ] = None,
) -> Annotated[dict, "The chats to which the current user is a member of."]:
    """List the Microsoft Teams chats to which the current user is a member of."""
    limit = min(50, max(1, limit))

    client = get_client(context.get_auth_token_or_empty())

    response = await client.me.chats.get(
        chats_request(
            top=limit,
            next_page_token=next_page_token,
            expand=["members", "lastMessagePreview"],
        )
    )

    response = cast(ChatCollectionResponse, response)

    chats = [serialize_chat(chat) for chat in cast(list[Chat], response.value)]

    return {
        "chats": chats,
        "count": len(chats),
        "pagination": build_token_pagination(response),
    }


@tool(requires_auth=Microsoft(scopes=["ChatMessage.Send"]))
async def send_message_to_chat(
    context: ToolContext,
    message: Annotated[str, "The message to send to the chat."],
    chat_id: Annotated[str | None, "The ID of the chat to send the message."] = None,
    user_ids: Annotated[
        list[str] | None, "The IDs of the users in the chat to send the message."
    ] = None,
    user_names: Annotated[
        list[str] | None,
        "The names of the users in the chat to send the message. Prefer providing user_ids, "
        "when available, since the performance is better.",
    ] = None,
) -> Annotated[dict, "The message that was sent."]:
    """Sends a message to a Microsoft Teams chat.

    Provide exactly one of chat_id or user_ids/user_names. When available, prefer providing a
    chat_id or user_ids for optimal performance.

    If the user provides user name(s), DO NOT CALL THE `Teams.SearchUsers` or `Teams.SearchPeople`
    tools first. Instead, provide the user name(s) directly to this tool through the `user_names`
    argument. It is not necessary to provide the currently signed in user's name/id, so do not call
    `Teams.GetSignedInUser` before calling this tool either.
    """
    if chat_id and chat_id.endswith("@thread.v2"):
        from arcade_microsoft_teams.tools.channel import send_message_to_channel

        message = (
            f"chat_id must be a Microsoft Teams chat ID. The value '{chat_id}' is a Channel ID. "
            f"Use the `MicrosoftTeams.{send_message_to_channel.__tool_name__}` tool instead."
        )
        raise ToolExecutionError(message=message, developer_message=message)

    if not chat_id:
        chat = await get_chat_metadata(context, user_ids=user_ids, user_names=user_names)
        chat_id = chat["chat"]["id"]

    client = get_client(context.get_auth_token_or_empty())
    response = await client.chats.by_chat_id(cast(str, chat_id)).messages.post(
        ChatMessage(body=ItemBody(content=message))
    )

    if not isinstance(response, ChatMessage):
        return {"message": None}

    return {
        "status": "Message successfully sent.",
        "message": serialize_chat_message(response),
    }


@tool(requires_auth=Microsoft(scopes=["ChatMessage.Send"]))
async def reply_to_chat_message(
    context: ToolContext,
    reply_content: Annotated[str, "The content of the reply message."],
    message_id: Annotated[str, "The ID of the message to reply to."],
    chat_id: Annotated[str | None, "The ID of the chat to send the message."] = None,
    user_ids: Annotated[
        list[str] | None, "The IDs of the users in the chat to send the message."
    ] = None,
    user_names: Annotated[
        list[str] | None,
        "The names of the users in the chat to send the message. Prefer providing user_ids, "
        "when available, since the performance is better.",
    ] = None,
) -> Annotated[dict, "The reply message that was sent."]:
    """Sends a reply to a Microsoft Teams chat message.

    Provide exactly one of chat_id or user_ids/user_names. When available, prefer providing a
    chat_id or user_ids for optimal performance.

    If the user provides user name(s), DO NOT CALL THE `Teams.SearchUsers` or `Teams.SearchPeople`
    tools first. Instead, provide the user name(s) directly to this tool through the `user_names`
    argument. It is not necessary to provide the currently signed in user's name/id, so do not call
    `Teams.GetSignedInUser` before calling this tool either.
    """
    if chat_id and chat_id.endswith("@thread.v2"):
        from arcade_microsoft_teams.tools.channel import reply_to_channel_message

        message = (
            f"chat_id must be a Microsoft Teams chat ID. The value '{chat_id}' is a Channel ID. "
            f"Use the `MicrosoftTeams.{reply_to_channel_message.__tool_name__}` tool instead."
        )
        raise ToolExecutionError(message=message, developer_message=message)

    if not chat_id:
        chat = await get_chat_metadata(context, user_ids=user_ids, user_names=user_names)
        chat_id = chat["chat"]["id"]

    original_msg_response = await get_chat_message_by_id(
        context=context,
        message_id=message_id,
        chat_id=chat_id,
    )

    if not original_msg_response["message"]:
        raise ToolExecutionError(
            message="Original message not found with id: " + message_id,
            developer_message="Original message not found with id: " + message_id,
        )

    original_msg = populate_message_for_reply(original_msg_response["message"])
    reply_body = build_reply_body_from_original_message(original_msg, reply_content)

    client = get_client(context.get_auth_token_or_empty())
    response = await client.chats.by_chat_id(cast(str, chat_id)).messages.post(
        ChatMessage(
            body=ItemBody(
                content=reply_body,
                content_type=BodyType.Html,
            ),
            attachments=[
                ChatMessageAttachment(
                    id=original_msg["id"],
                    content=json.dumps(original_msg["content_dict"]),
                    content_type="reference",
                ),
            ],
        )
    )

    if not isinstance(response, ChatMessage):
        error_msg = (
            "Unable to parse Microsoft Teams API response from the message reply request. "
            "Cannot determine whether the message reply was successfully sent or not."
        )
        raise ToolExecutionError(message=error_msg, developer_message=error_msg)

    return {
        "success": True,
        "status": "Message reply successfully sent.",
        "message": serialize_chat_message(response),
    }


@tool(requires_auth=Microsoft(scopes=["Chat.Create"]))
async def create_chat(
    context: ToolContext,
    user_ids: Annotated[list[str] | None, "The IDs of the users to create a chat with."] = None,
    user_names: Annotated[list[str] | None, "The names of the users to create a chat with."] = None,
) -> Annotated[dict, "The chat that was created."]:
    """Creates a Microsoft Teams chat.

    If the chat already exists with the specified members, the MS Graph API will return the
    existing chat.

    Provide any combination of user_ids and/or user_names. When available, prefer providing
    user_ids for optimal performance.
    """
    if not any([user_ids, user_names]):
        message = "At least one of user_ids or user_names must be provided."
        raise ToolExecutionError(message=message, developer_message=message)

    user_ids_with_current_user = await add_current_user_id(context, user_ids)

    if user_names:
        users_by_name = await find_humans_by_name(context, user_names)
        user_ids_with_current_user.extend([user["id"] for user in users_by_name])

    client = get_client(context.get_auth_token_or_empty())
    response = await client.chats.post(
        create_chat_request(
            members=[
                build_conversation_member(user_id=user_id) for user_id in user_ids_with_current_user
            ]
        )
    )

    return {"chat": serialize_chat(cast(Chat, response))}
