"""Tests for API filtering utilities."""

from collections.abc import Callable
from unittest.mock import AsyncMock, Mock

import pytest
from arcade_tdk import ToolContext
from msgraph.generated.models.chat_collection_response import ChatCollectionResponse

from arcade_microsoft_teams.api_filtering_utils import (
    _build_member_filter_query_by_display_name,
    filter_chats_by_member_display_names_exact,
    filter_chats_with_odata_filter,
)


class TestFilterChatsByMemberDisplayNames:
    @pytest.mark.asyncio
    async def test_filter_chats_by_exact_members(
        self,
        mock_context: ToolContext,
        mock_client: Mock,
        chat_factory: Callable,
        member_factory: Callable,
    ) -> None:
        # Chat with exactly the members we're looking for
        chat1 = chat_factory(
            members=[
                member_factory(display_name="John Doe"),
                member_factory(display_name="Jane Smith"),
            ]
        )
        # Chat with additional member (should be filtered out)
        chat2 = chat_factory(
            members=[
                member_factory(display_name="John Doe"),
                member_factory(display_name="Jane Smith"),
                member_factory(display_name="Bob Johnson"),
            ]
        )

        mock_response = ChatCollectionResponse()
        mock_response.value = [chat1, chat2]
        mock_response.odata_next_link = None

        mock_client.me.chats.get = AsyncMock(return_value=mock_response)

        result = await filter_chats_by_member_display_names_exact(
            context=mock_context,
            display_names=["John Doe", "Jane Smith"],
        )

        # Should only return chat1 as it has exactly the members specified
        assert len(result) == 1
        assert result[0].id == chat1.id

        # Verify filter string was set correctly
        call_args = mock_client.me.chats.get.call_args
        request_config = call_args[1]["request_configuration"]
        expected_filter = (
            "members/any(m0:m0/displayName eq 'John Doe') and "
            "members/any(m1:m1/displayName eq 'Jane Smith')"
        )
        assert request_config.query_parameters.filter == expected_filter

    @pytest.mark.asyncio
    async def test_filter_chats_empty_display_names(
        self,
        mock_context: ToolContext,
        mock_client: Mock,
    ) -> None:
        result = await filter_chats_by_member_display_names_exact(
            context=mock_context,
            display_names=[],
        )

        assert result == []
        mock_client.me.chats.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_filter_chats_returns_max_50(
        self,
        mock_context: ToolContext,
        mock_client: Mock,
        chat_factory: Callable,
        member_factory: Callable,
    ) -> None:
        # Create 60 chats with exact match
        chats = [
            chat_factory(
                members=[
                    member_factory(display_name="User A"),
                    member_factory(display_name="User B"),
                ]
            )
            for _ in range(60)
        ]

        mock_response = ChatCollectionResponse()
        mock_response.value = chats[:50]  # API returns max 50
        mock_response.odata_next_link = None

        mock_client.me.chats.get = AsyncMock(return_value=mock_response)

        result = await filter_chats_by_member_display_names_exact(
            context=mock_context,
            display_names=["User A", "User B"],
        )

        assert len(result) == 50

        # Verify top parameter was set to 50
        call_args = mock_client.me.chats.get.call_args
        request_config = call_args[1]["request_configuration"]
        assert request_config.query_parameters.top == 50


class TestFilterChatsWithODataFilter:
    @pytest.mark.asyncio
    async def test_filter_chats_with_odata_filter(
        self,
        mock_context: ToolContext,
        mock_client: Mock,
        chat_factory: Callable,
    ) -> None:
        chat1 = chat_factory()
        chat1.topic = "Project Alpha"
        chat2 = chat_factory()
        chat2.topic = "Project Beta"

        mock_response = ChatCollectionResponse()
        mock_response.value = [chat1]
        mock_response.odata_next_link = None

        mock_client.me.chats.get = AsyncMock(return_value=mock_response)

        result = await filter_chats_with_odata_filter(
            context=mock_context,
            filter_string="topic eq 'Project Alpha'",
        )

        assert len(result) == 1
        assert result[0].id == chat1.id

        # Verify the filter was passed correctly
        call_args = mock_client.me.chats.get.call_args
        request_config = call_args[1]["request_configuration"]
        assert request_config.query_parameters.filter == "topic eq 'Project Alpha'"
        assert request_config.query_parameters.expand == ["members"]
        assert request_config.query_parameters.orderby == [
            "lastMessagePreview/createdDateTime desc"
        ]

    @pytest.mark.asyncio
    async def test_filter_chats_with_semaphore(
        self,
        mock_context: ToolContext,
        mock_client: Mock,
        chat_factory: Callable,
    ) -> None:
        import asyncio

        chat = chat_factory()
        mock_response = ChatCollectionResponse()
        mock_response.value = [chat]
        mock_response.odata_next_link = None

        mock_client.me.chats.get = AsyncMock(return_value=mock_response)

        semaphore = asyncio.Semaphore(1)
        result = await filter_chats_with_odata_filter(
            context=mock_context,
            filter_string="chatType eq 'oneOnOne'",
            semaphore=semaphore,
        )

        assert len(result) == 1
        assert result[0].id == chat.id
        mock_client.me.chats.get.assert_called_once()


class TestBuildMemberFilterQuery:
    def test_build_filter_single_display_name(self) -> None:
        result = _build_member_filter_query_by_display_name(["John Doe"])
        assert result == "members/any(m0:m0/displayName eq 'John Doe')"

    def test_build_filter_multiple_display_names(self) -> None:
        result = _build_member_filter_query_by_display_name([
            "John Doe",
            "Jane Smith",
            "Bob Johnson",
        ])
        expected = (
            "members/any(m0:m0/displayName eq 'John Doe') and "
            "members/any(m1:m1/displayName eq 'Jane Smith') and "
            "members/any(m2:m2/displayName eq 'Bob Johnson')"
        )
        assert result == expected

    def test_build_filter_escapes_single_quotes(self) -> None:
        result = _build_member_filter_query_by_display_name(["John O'Brien"])
        assert result == "members/any(m0:m0/displayName eq 'John O''Brien')"

    def test_build_filter_empty_list(self) -> None:
        result = _build_member_filter_query_by_display_name([])
        assert result == ""
