from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any, cast

from msgraph.generated.models.chat import Chat
from msgraph.generated.models.conversation_member import ConversationMember

from arcade_microsoft_teams.exceptions import MatchHumansByNameRetryableError


class HumanNameMatchType(Enum):
    EXACT = "exact"
    PARTIAL = "partial"
    NOT_FOUND = "not_found"


class ChatMembershipMatchType(Enum):
    EXACT_MATCH = "exact_match"
    PARTIAL_MATCH = "partial_match"


class PaginationSentinel(ABC):
    """Base class for pagination sentinel classes."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    @abstractmethod
    def __call__(self, last_result: Any) -> bool | tuple[bool, list[Any]]:
        """Determine if the pagination should stop."""
        raise NotImplementedError


class FindChatByMembersSentinel(PaginationSentinel):
    def __init__(self, user_ids: list[str] | None = None, user_names: list[str] | None = None):
        self._user_ids = user_ids or []
        self._user_names = user_names or []
        self._expected_member_count = len(self.user_ids) + len(self.user_names)
        self.matches: dict[ChatMembershipMatchType, list[Chat]] = {
            ChatMembershipMatchType.EXACT_MATCH: [],
            ChatMembershipMatchType.PARTIAL_MATCH: [],
        }

    @property
    def user_ids(self) -> list[str]:
        return self._user_ids

    @property
    def user_names(self) -> list[str]:
        return self._user_names

    @property
    def expected_member_count(self) -> int:
        return self._expected_member_count

    @property
    def exact_matches(self) -> list[Chat]:
        return self.matches[ChatMembershipMatchType.EXACT_MATCH]

    @property
    def partial_matches(self) -> list[Chat]:
        return self.matches[ChatMembershipMatchType.PARTIAL_MATCH]

    def __call__(self, last_result: Any) -> bool:
        if len(self.matches[ChatMembershipMatchType.EXACT_MATCH]) > 0:
            return True

        for chat in last_result:
            match_type = self.chat_members_match(chat)
            if match_type:
                self.matches[match_type].append(chat)

        return len(self.matches[ChatMembershipMatchType.EXACT_MATCH]) > 0

    def chat_members_match(self, chat: Chat) -> ChatMembershipMatchType | None:
        # First we check if the member list length matches
        if isinstance(chat.members, list) and len(chat.members) != self.expected_member_count:
            return None

        members = cast(list[ConversationMember], chat.members)
        members_by_user_id: dict[str, ConversationMember] = {}

        for member in members:
            if hasattr(member, "user_id"):
                members_by_user_id[getattr(member, "user_id")] = member  # noqa: B009

        # Check the user_ids
        member_user_ids = set(members_by_user_id.keys())
        for user_id in self.user_ids:
            if user_id in member_user_ids:
                del members_by_user_id[user_id]
            # If the user_id is not in the member list, it's not a match
            else:
                return None

        # Check the user_names
        match_type, user_ids_not_matched = self.check_usernames_match_chat_members(
            members_by_user_id
        )

        # If there are any members not matched by user_names, the chat is not a match
        if user_ids_not_matched:
            return None

        return match_type

    def check_usernames_match_chat_members(
        self, members_by_user_id: dict[str, ConversationMember]
    ) -> tuple[ChatMembershipMatchType, set[str]]:
        members_by_user_id = deepcopy(members_by_user_id)
        user_ids_not_matched = set(members_by_user_id.keys())
        has_partial_match = False

        for user_name in self.user_names:
            for user_id, member in members_by_user_id.items():
                if not isinstance(member.display_name, str):
                    continue

                if member.display_name.casefold() == user_name.casefold():
                    del members_by_user_id[user_id]
                    user_ids_not_matched.remove(user_id)
                    break
                elif user_name.casefold() in member.display_name.casefold():
                    has_partial_match = True
                    del members_by_user_id[user_id]
                    user_ids_not_matched.remove(user_id)
                    break

        match_type = (
            ChatMembershipMatchType.PARTIAL_MATCH
            if has_partial_match
            else ChatMembershipMatchType.EXACT_MATCH
        )

        return match_type, user_ids_not_matched


@dataclass
class HumanNameMatch:
    human: dict
    match_type: HumanNameMatchType


class MatchHumansByName:
    def __init__(self, names: list[str], users: list[dict], people: list[dict]):
        self.matches_by_name: dict[str, list[HumanNameMatch]] = {}
        self.names = names
        self.users = users
        self.people = people
        self._human_id_matched: dict[str, set[str]] = {name: set() for name in names}

    def _human_name(self, human: dict) -> str:
        if isinstance(human["name"].get("display"), str):
            return cast(str, human["name"]["display"].casefold())
        else:
            name_parts = []

            if isinstance(human["name"].get("first"), str):
                name_parts.append(human["name"]["first"])
            if isinstance(human["name"].get("last"), str):
                name_parts.append(human["name"]["last"])

            if not name_parts:
                return ""

            return " ".join(name_parts).casefold()

    def run(self) -> None:
        for name in self.names:
            name_lower = name.casefold()
            self.matches_by_name[name] = []
            for user in self.users:
                user_name = self._human_name(user)
                if name_lower == user_name:
                    self.add_exact_match(name, user)
                elif name_lower in user_name:
                    self.add_partial_match(name, user)

            for person in self.people:
                person_name = self._human_name(person)
                if name_lower == person_name:
                    self.add_exact_match(name, person)
                elif name_lower in person_name:
                    self.add_partial_match(name, person)

    def add_exact_match(self, name: str, human: dict) -> None:
        if human["id"] in self._human_id_matched[name]:
            return

        human_match = HumanNameMatch(human=human, match_type=HumanNameMatchType.EXACT)
        self.matches_by_name[name].append(human_match)
        self._human_id_matched[name].add(human["id"])

    def add_partial_match(self, name: str, human: dict) -> None:
        if human["id"] in self._human_id_matched[name]:
            return

        human_match = HumanNameMatch(human=human, match_type=HumanNameMatchType.PARTIAL)
        self.matches_by_name[name].append(human_match)
        self._human_id_matched[name].add(human["id"])

    def get_unique_exact_matches(self, max_matches_per_name: int = 10) -> list[dict]:
        unique_exact_matches = []
        match_errors = []

        for name, matches in self.matches_by_name.items():
            exact_matches = []
            partial_matches = []
            human_ids_matched = set()
            for human_match in matches:
                if human_match.human["id"] in human_ids_matched:
                    continue

                if human_match.match_type == HumanNameMatchType.EXACT:
                    exact_matches.append(human_match.human)
                    # If we already found an exact match with this human id, we skip other matches
                    human_ids_matched.add(human_match.human["id"])
                else:
                    partial_matches.append(human_match.human)

            # If there is a single exact match, we ignore partial matches, if any
            if len(exact_matches) == 1:
                unique_exact_matches.append(exact_matches[0])

            # If there are none or multiple exact matches, we add this name to match errors
            else:
                # If multiple exact matches, we can ignore the partial ones
                final_matches = exact_matches or partial_matches
                match_error = {
                    "name": name,
                    "matches": final_matches[:max_matches_per_name],
                }
                if len(final_matches) > max_matches_per_name:
                    match_error["message"] = (
                        f"Too many matches found for '{name}'. "
                        f"Truncated to the first {max_matches_per_name} matches."
                    )
                match_errors.append(match_error)

        if match_errors:
            raise MatchHumansByNameRetryableError(match_errors)

        return unique_exact_matches
