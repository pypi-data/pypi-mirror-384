import asyncio
import datetime
import json
import re
import uuid
from collections.abc import Callable
from copy import deepcopy
from typing import Any, cast

from arcade_tdk import ToolContext
from arcade_tdk.errors import RetryableToolError, ToolExecutionError
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.chats.chats_request_builder import ChatsRequestBuilder
from msgraph.generated.chats.item.messages.messages_request_builder import MessagesRequestBuilder
from msgraph.generated.models.aad_user_conversation_member import AadUserConversationMember
from msgraph.generated.models.channel import Channel
from msgraph.generated.models.chat import Chat
from msgraph.generated.models.chat_type import ChatType
from msgraph.generated.models.user import User
from msgraph.generated.teams.item.all_channels.all_channels_request_builder import (
    AllChannelsRequestBuilder,
)
from msgraph.generated.teams.item.members.members_request_builder import (
    MembersRequestBuilder,
)
from msgraph.generated.teams.teams_request_builder import TeamsRequestBuilder
from msgraph.generated.users.item.people.people_request_builder import PeopleRequestBuilder
from msgraph.generated.users.users_request_builder import UsersRequestBuilder

from arcade_microsoft_teams.api_filtering_utils import (
    filter_chats_by_member_display_names_exact,
)
from arcade_microsoft_teams.client import get_client
from arcade_microsoft_teams.concurency import paginate
from arcade_microsoft_teams.constants import (
    ENV_VARS,
    MatchType,
    PartialMatchType,
)
from arcade_microsoft_teams.exceptions import MultipleItemsFoundError, NoItemsFoundError
from arcade_microsoft_teams.models import (
    MatchHumansByName,
)
from arcade_microsoft_teams.serializers import serialize_chat, short_version


def remove_none_values(kwargs: dict) -> dict:
    return {key: val for key, val in kwargs.items() if val is not None}


def load_config_param(context: ToolContext, key: str) -> Any:
    try:
        return context.get_metadata(key)
    except ValueError:
        pass

    try:
        return context.get_secret(key)
    except ValueError:
        pass

    return ENV_VARS.get(key)


def validate_datetime_string(value: str) -> str:
    datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return value


def validate_datetime_range(start: str | None, end: str | None) -> tuple[str | None, str | None]:
    invalid_datetime_msg = (
        "Invalid {field} datetime string: {value}. "
        "Provide a string in the format 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'."
    )
    start_dt = None
    end_dt = None
    if start:
        try:
            start_dt = validate_datetime_string(start)
        except ValueError as e:
            raise ToolExecutionError(
                invalid_datetime_msg.format(field="start_datetime", value=start)
            ) from e
    if end:
        try:
            end_dt = validate_datetime_string(end)
        except ValueError as e:
            raise ToolExecutionError(
                invalid_datetime_msg.format(field="end_datetime", value=end)
            ) from e
    if start_dt and end_dt and start_dt > end_dt:
        err_msg = "start_datetime must be before end_datetime."
        raise ToolExecutionError(message=err_msg, developer_message=err_msg)
    return start, end


def is_id(value: str) -> bool:
    return is_teams_id(value) or is_guid(value) or is_channel_id(value)


def is_teams_id(value: str) -> bool:
    return bool(re.match(r"^19:[\w\d]+@thread\.v2$", value))


def is_channel_id(value: str) -> bool:
    return bool(re.match(r"^19:[\w\d]+@[\w\d.]+$", value))


def is_guid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    else:
        return True


def config_request(
    request_builder: Callable,
    **kwargs: Any,
) -> RequestConfiguration:
    kwargs = remove_none_values(kwargs)
    if "next_page_token" in kwargs:
        kwargs["skiptoken"] = kwargs.pop("next_page_token")
    query_params = request_builder(**kwargs)
    return RequestConfiguration(query_parameters=query_params)


def teams_request(top: int, filter_: str | None, skiptoken: str | None) -> RequestConfiguration:
    return config_request(
        TeamsRequestBuilder.TeamsRequestBuilderGetQueryParameters,
        top=top,
        filter=filter_,
        skiptoken=skiptoken,
    )


def channels_request(select: list[str] | None) -> RequestConfiguration:
    return config_request(
        AllChannelsRequestBuilder.AllChannelsRequestBuilderGetQueryParameters,
        select=select,
    )


def members_request(top: int, filter_: str | None = None) -> RequestConfiguration:
    return config_request(
        MembersRequestBuilder.MembersRequestBuilderGetQueryParameters, top=top, filter=filter_
    )


def messages_request(**kwargs: Any) -> RequestConfiguration:
    kwargs = remove_none_values(kwargs)
    return config_request(MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters, **kwargs)


def people_request(
    top: int,
    next_page_token: str | None,
    search: str | None,
) -> RequestConfiguration:
    return config_request(
        PeopleRequestBuilder.PeopleRequestBuilderGetQueryParameters,
        top=top,
        next_page_token=next_page_token,
        search=search,
    )


def users_request(**kwargs: Any) -> RequestConfiguration:
    return config_request(UsersRequestBuilder.UsersRequestBuilderGetQueryParameters, **kwargs)


def chats_request(
    top: int,
    next_page_token: str | None,
    expand: list[str] | None,
) -> RequestConfiguration:
    kwargs = {
        "top": top,
        "next_page_token": next_page_token,
        "expand": expand,
    }
    return config_request(ChatsRequestBuilder.ChatsRequestBuilderGetQueryParameters, **kwargs)


def create_chat_request(members: list[AadUserConversationMember]) -> Chat:
    return Chat(
        chat_type=ChatType.OneOnOne if len(members) == 2 else ChatType.Group,
        # The Chat.members expect a list[ConversationMember], but we actually
        # need to pass a list[AadUserConversationMember]
        members=members,  # type: ignore[arg-type]
    )


def build_conversation_member(
    user_id: str, roles: list[str] | None = None
) -> AadUserConversationMember:
    roles = roles or ["owner"]
    return AadUserConversationMember(
        odata_type="#microsoft.graph.aadUserConversationMember",
        roles=roles,
        additional_data={"user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{user_id}')"},
    )


def build_token_pagination(response: Any) -> dict:
    pagination = {"is_last_page": True}
    if response.odata_next_link:
        pagination["is_last_page"] = False
        pagination["next_page_token"] = response.odata_next_link
    return pagination


def build_offset_pagination(
    items: list, limit: int, offset: int, more_results: bool | None = None
) -> dict:
    if isinstance(more_results, bool):
        is_last_page = not more_results
    else:
        is_last_page = len(items) < limit or offset + limit >= 999

    pagination = {
        "is_last_page": is_last_page,
        "limit": limit,
        "current_offset": offset,
    }
    if not is_last_page:
        pagination["next_offset"] = offset + len(items)
    return pagination


def build_people_search_clause(
    keywords: list[str],
    match_type: PartialMatchType,
) -> str:
    operator = match_type.to_filter_condition().value
    return f" {operator} ".join([f'"{keyword}"' for keyword in keywords])


def build_users_search_clause(
    keywords: list[str],
    match_type: PartialMatchType,
) -> str:
    operator = match_type.to_filter_condition().value
    return f" {operator} ".join([f'"displayName:{keyword}"' for keyword in keywords])


def build_filter_clause(
    field: str,
    keywords: str,
    match_type: MatchType,
) -> str:
    if match_type == MatchType.EXACT:
        return f"{field} eq '{keywords.casefold()}'"
    words = keywords.casefold().split()
    condition = f" {match_type.to_filter_condition().value} "
    return condition.join(f"startswith({field}, '{word.strip()}')" for word in words)


def build_startswith_filter_clause(
    field: str,
    starts_with: str,
    use_case_variants: bool = False,
) -> str:
    if not use_case_variants:
        return f"startswith({field}, '{starts_with}')"

    variants = generate_case_variants(starts_with)
    return " or ".join(f"startswith({field}, '{variant.strip()}')" for variant in variants)


def filter_by_name_or_description(
    keywords: str,
    match_type: MatchType,
) -> str:
    if match_type == MatchType.EXACT:
        return build_filter_clause("displayName", keywords, match_type)

    name_filter = build_filter_clause("displayName", keywords, match_type)
    description_filter = build_filter_clause("description", keywords, match_type)
    return f"{name_filter} or {description_filter}"


async def resolve_team_id(context: ToolContext, team_id_or_name: str | None) -> str:
    if not team_id_or_name:
        team = await find_unique_user_team(context=context)
        return cast(str, team["id"])

    if is_id(team_id_or_name):
        return team_id_or_name

    team = await find_unique_team_by_name(context=context, name=team_id_or_name)
    return cast(str, team["id"])


async def find_unique_user_team(context: ToolContext) -> dict:
    from arcade_microsoft_teams.tools.teams import list_teams  # Avoid circular import

    response = await list_teams(context)
    teams = response["teams"]
    if len(teams) == 0:
        raise NoItemsFoundError("teams")
    if len(teams) > 1:
        raise MultipleItemsFoundError("teams", [short_version(team) for team in teams])
    return cast(dict, teams[0])


async def find_unique_team_by_name(context: ToolContext, name: str) -> dict:
    from arcade_microsoft_teams.tools.teams import search_teams  # Avoid circular import

    response = await search_teams(
        context=context,
        team_name_starts_with=name,
        limit=1,
    )
    teams = response["teams"]
    if len(teams) == 0:
        raise NoItemsFoundError("teams")
    elif len(teams) > 1:
        raise MultipleItemsFoundError("teams", [short_version(team) for team in teams])
    return cast(dict, teams[0])


async def resolve_channel_id(
    context: ToolContext,
    team_id: str,
    channel_id_or_name: str | None,
) -> str:
    if not channel_id_or_name:
        channel = await find_unique_channel(context, team_id)
        return cast(str, channel["id"])

    if is_channel_id(channel_id_or_name):
        return channel_id_or_name

    channel = await find_unique_channel_by_name(context, team_id, channel_id_or_name)
    return cast(str, channel["id"])


async def find_unique_channel(context: ToolContext, team_id: str) -> dict:
    from toolkits.teams.arcade_microsoft_teams.tools.channel import (
        list_channels,  # Avoid circular import
    )

    response = await list_channels(context, team_id)
    channels = response["channels"]
    if len(channels) == 0:
        raise NoItemsFoundError("channels")
    if len(channels) > 1:
        raise MultipleItemsFoundError("channels", channels)
    return cast(dict, channels[0])


async def find_unique_channel_by_name(context: ToolContext, team_id: str, name: str) -> dict:
    from arcade_microsoft_teams.tools.channel import search_channels  # Avoid circular import

    response = await search_channels(
        context=context,
        team_id_or_name=team_id,
        keywords=[name],
        match_type=MatchType.PARTIAL_ANY,
    )
    channels = response["channels"]

    if len(channels) == 1:
        return cast(dict, channels[0])

    elif len(channels) == 0:
        raise NoItemsFoundError(
            item="channels",
            available_options=channels,
            search_term=name,
        )

    else:
        for channel in channels:
            if channel["name"].casefold() == name.casefold():
                return cast(dict, channel)
        raise MultipleItemsFoundError(
            item="channels",
            available_options=channels,
            search_term=name,
        )


async def find_chat_by_users(
    context: ToolContext,
    user_ids: list[str] | None,
    user_names: list[str] | None,
    semaphore: asyncio.Semaphore | None = None,
) -> dict:
    user_ids = cast(list[str], user_ids or [])
    user_names = cast(list[str], user_names or [])

    if not user_ids and not user_names:
        error = (
            "The user_ids and user_names arguments are empty. "
            "Provide at least one of user_ids or user_names or a combination of both."
        )
        raise ToolExecutionError(message=error, developer_message=error)

    user_info_map = {}

    if user_names:
        users_from_names = await find_humans_by_name(context, user_names)
        for user in users_from_names:
            display_name = ""
            if "name" in user and isinstance(user["name"], dict):
                display_name = user["name"].get("display", "")
            user_info_map[user["id"]] = display_name

    user_info_map = await _get_user_display_name_mapping(
        context, user_ids, user_info_map, semaphore
    )

    if not user_info_map:
        return {}

    if len(user_info_map) > 20:
        raise ToolExecutionError(
            message="Cannot filter by more than 20 users",
            developer_message=(
                f"Attempted to filter by {len(user_info_map)} users, but the limit is 20"
            ),
        )

    display_names = list(user_info_map.values())

    chats = await filter_chats_by_member_display_names_exact(context, display_names, semaphore)

    if not chats:
        return {}

    return serialize_chat(chats[0])


async def find_humans_by_name(
    context: ToolContext,
    names: list[str],
    semaphore: asyncio.Semaphore | None = None,
) -> list[dict]:
    if not names:
        message = "No names provided"
        raise ToolExecutionError(message=message, developer_message=message)

    semaphore = semaphore or asyncio.Semaphore(load_config_param(context, "TEAMS_MAX_CONCURRENCY"))
    names = deduplicate_names(names)

    # Avoid circular import
    from arcade_microsoft_teams.serializers import serialize_person
    from arcade_microsoft_teams.tools.users import search_users

    client = get_client(context.get_auth_token_or_empty())

    async with semaphore:
        users_response, (people, _) = await asyncio.gather(
            search_users(
                context=context,
                keywords=names,
                match_type=PartialMatchType.PARTIAL_ANY,
                limit=999,  # The MS Graph API does not support more than 999 users
            ),
            paginate(
                context=context,
                func=client.me.people.get,
                request_builder=people_request,
                page_limit=100,
                semaphore=semaphore,
                search=build_people_search_clause(names, PartialMatchType.PARTIAL_ANY),
            ),
        )

    match_humans_by_name = MatchHumansByName(
        names=names,
        users=users_response["users"],
        people=[serialize_person(person) for person in people],
    )

    match_humans_by_name.run()

    return match_humans_by_name.get_unique_exact_matches(max_matches_per_name=10)


def _matches_channel_name(channel_name: str, keywords: list[str], match_type: MatchType) -> bool:
    channel_name = channel_name.casefold()
    if match_type == MatchType.EXACT:
        return any(channel_name == keyword.casefold() for keyword in keywords)
    if match_type == MatchType.PARTIAL_ALL:
        return all(keyword.casefold() in channel_name for keyword in keywords)
    return any(keyword.casefold() in channel_name for keyword in keywords)


def filter_channels_by_name(
    channels: list[Channel],
    keywords: list[str],
    match_type: MatchType,
    serializer: Callable | None = None,
) -> list[Channel]:
    serializer = serializer or (lambda x: x)
    return [
        serializer(channel)
        for channel in channels
        if _matches_channel_name(cast(str, channel.display_name), keywords, match_type)
    ]


def deduplicate_names(names: list[str]) -> list[str]:
    names_unique = []
    names_casefold = {name.casefold() for name in names}
    for name in names:
        name_lower = name.casefold()
        if name_lower in names_casefold:
            names_unique.append(name)
            names_casefold.remove(name_lower)
    return names_unique


def generate_case_variants(keyword: str) -> list[str]:
    return [
        keyword,
        keyword.casefold(),
        keyword.upper(),
        keyword.title(),
        keyword.capitalize(),
    ]


def match_user_by_name(user: User, keywords: list[str], match_type: PartialMatchType) -> bool:
    if not user.display_name:
        return False

    user_name = user.display_name.casefold()
    if match_type == PartialMatchType.PARTIAL_ALL:
        return all(keyword.casefold() in user_name for keyword in keywords)
    else:
        return any(keyword.casefold() in user_name for keyword in keywords)


def raise_for_humans_not_found(
    not_found: list[str],
    not_matched: list[dict],
) -> None:
    # Avoid circular import
    from arcade_microsoft_teams.serializers import short_human
    from arcade_microsoft_teams.tools.people import search_people
    from arcade_microsoft_teams.tools.users import search_users

    max_items = 50
    message = f"Could not find the following users: {', '.join(not_found)}"
    available_humans = [short_human(human) for human in not_matched[0:max_items]]
    additional_prompt = f"Available users/people: {json.dumps(available_humans)}"
    if len(available_humans) > max_items:
        additional_prompt = (
            "Some of the available users/people are listed next. To retrieve more, use the "
            f"Teams.{search_users.__tool_name__} or Teams.{search_people.__tool_name__} tools. "
            f"{additional_prompt}"
        )
    raise RetryableToolError(
        message=message,
        developer_message=message,
        additional_prompt_content=additional_prompt,
    )


async def add_current_user_id(context: ToolContext, user_ids: list[str] | None) -> list[str]:
    from arcade_microsoft_teams.tools.users import get_signed_in_user  # Avoid circular import

    current_user = await get_signed_in_user(context)
    user_ids = cast(list[str], user_ids or [])
    if current_user["id"] not in user_ids:
        user_ids.append(current_user["id"])
    return list(set(user_ids))


def populate_message_for_reply(original_msg: dict) -> dict:
    message = deepcopy(original_msg)
    message["preview"] = build_original_message_preview(original_msg)
    message["sender"] = build_original_message_sender(original_msg)

    message["content_dict"] = {
        "messageId": message["id"],
        "messagePreview": message["preview"],
        "messageSender": message["sender"],
    }

    return message


def build_original_message_preview(original_msg: dict) -> str:
    if original_msg["content"].get("summary"):
        return cast(str, original_msg["content"]["summary"])
    else:
        if original_msg["content"]["type"] == "html":
            text = strip_html_tags(cast(str, original_msg["content"]["text"]))
        else:
            text = cast(str, original_msg["content"]["text"])
        return text[:97] + "..." if len(text) > 100 else text


def build_original_message_sender(original_msg: dict) -> dict[str, Any]:
    if original_msg.get("author") and original_msg["author"].get("user"):
        return {
            "application": None,
            "device": None,
            "conversation": None,
            "tag": None,
            "user": {
                "userIdentityType": "aadUser",
                "id": original_msg["author"]["user_id"],
                "displayName": original_msg["author"]["user_name"],
            },
        }
    else:
        return {}


def build_reply_body_from_original_message(
    original_msg: dict,
    reply_content: str,
) -> str:
    msg_id = original_msg["id"]
    preview = original_msg["preview"]
    author_id = original_msg["author"]["user_id"]
    author_name = original_msg["author"]["user_name"]
    return f"""
        <attachment id="{msg_id}"></attachment>
        <blockquote
            itemscope
            itemtype="http://schema.skype.com/Reply"
            itemid="{msg_id}">
            <strong itemprop="mri" itemid="{author_id}">
                {author_name}
            </strong>
            <span itemprop="time" itemid="{msg_id}"></span>
            <p itemprop="preview">{preview}</p>
        </blockquote>
        <p>{reply_content}</p>
    """


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from a string using regex."""
    clean = re.sub(r"<[^>]+>", "", text)
    return clean


async def _get_user_display_name_mapping(
    context: ToolContext,
    user_ids: list[str],
    existing_map: dict[str, str],
    semaphore: asyncio.Semaphore | None = None,
) -> dict[str, str]:
    """Get display names for user IDs not already in existing_map."""
    client = get_client(context.get_auth_token_or_empty())
    result = existing_map.copy()

    for user_id in user_ids:
        if user_id not in result:
            if semaphore:
                async with semaphore:
                    user = await client.users.by_user_id(user_id).get()
            else:
                user = await client.users.by_user_id(user_id).get()

            if user and user.display_name:
                result[user_id] = user.display_name

    return result
