from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from arcade_microsoft_teams.who_am_i_util import (
    _extract_user_info,
    _get_current_user,
    build_who_am_i_response,
)


class TestExtractUserInfo:
    def test_extract_user_info_with_complete_data(self) -> None:
        user_info: dict[str, Any] = {
            "id": "user-123",
            "display_name": "John Doe",
            "given_name": "John",
            "surname": "Doe",
            "user_principal_name": "john.doe@contoso.com",
            "mail": "john.doe@contoso.com",
            "job_title": "Software Engineer",
            "department": "Engineering",
            "office_location": "Building 1",
            "business_phones": ["+1-555-0123", "+1-555-0124"],
            "mobile_phone": "+1-555-0456",
            "preferred_language": "en-US",
            "account_enabled": True,
            "tenant_domain": "contoso.com",
        }

        result = _extract_user_info(user_info)

        assert result == {
            "user_id": "user-123",
            "display_name": "John Doe",
            "given_name": "John",
            "surname": "Doe",
            "user_principal_name": "john.doe@contoso.com",
            "mail": "john.doe@contoso.com",
            "job_title": "Software Engineer",
            "department": "Engineering",
            "office_location": "Building 1",
            "business_phones": ["+1-555-0123", "+1-555-0124"],
            "mobile_phone": "+1-555-0456",
            "preferred_language": "en-US",
            "account_enabled": True,
            "tenant_domain": "contoso.com",
        }

    def test_extract_user_info_with_minimal_data(self) -> None:
        user_info: dict[str, Any] = {
            "id": "user-456",
            "display_name": "Jane Smith",
            "user_principal_name": "jane.smith@example.org",
        }

        result = _extract_user_info(user_info)

        assert result == {
            "user_id": "user-456",
            "display_name": "Jane Smith",
            "user_principal_name": "jane.smith@example.org",
        }

    def test_extract_user_info_with_empty_data(self) -> None:
        user_info: dict[str, Any] = {}

        result = _extract_user_info(user_info)

        assert result == {}


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_get_current_user_success(self) -> None:
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.id = "user-123"
        mock_response.display_name = "Test User"
        mock_response.given_name = "Test"
        mock_response.surname = "User"
        mock_response.user_principal_name = "test.user@contoso.com"
        mock_response.mail = "test.user@contoso.com"
        mock_response.job_title = "Test Engineer"
        mock_response.department = "QA"
        mock_response.office_location = "Remote"
        mock_response.business_phones = ["+1-555-TEST"]
        mock_response.mobile_phone = "+1-555-MOBILE"
        mock_response.preferred_language = "en-US"
        mock_response.account_enabled = True

        mock_client.me.get.return_value = mock_response

        result = await _get_current_user(mock_client)

        assert result == {
            "id": "user-123",
            "display_name": "Test User",
            "given_name": "Test",
            "surname": "User",
            "user_principal_name": "test.user@contoso.com",
            "mail": "test.user@contoso.com",
            "job_title": "Test Engineer",
            "department": "QA",
            "office_location": "Remote",
            "business_phones": ["+1-555-TEST"],
            "mobile_phone": "+1-555-MOBILE",
            "preferred_language": "en-US",
            "account_enabled": True,
            "tenant_domain": "contoso.com",
        }

    @pytest.mark.asyncio
    async def test_get_current_user_with_none_response(self) -> None:
        mock_client = AsyncMock()
        mock_client.me.get.return_value = None

        result = await _get_current_user(mock_client)

        assert result == {}


class TestBuildWhoAmIResponse:
    @pytest.mark.asyncio
    @patch("arcade_microsoft_teams.who_am_i_util._get_current_user")
    async def test_build_who_am_i_response(self, mock_get_user: Mock) -> None:
        mock_client = AsyncMock()

        mock_get_user.return_value = {
            "id": "user-123",
            "display_name": "Integration Test User",
            "given_name": "Integration",
            "surname": "User",
            "user_principal_name": "integration.user@contoso.com",
            "mail": "integration.user@contoso.com",
            "job_title": "Test Engineer",
            "department": "QA",
            "office_location": "Remote",
            "business_phones": ["+1-555-TEST"],
            "mobile_phone": "+1-555-MOBILE",
            "preferred_language": "en-US",
            "account_enabled": True,
            "tenant_domain": "contoso.com",
        }

        result = await build_who_am_i_response(mock_client)

        mock_get_user.assert_called_once_with(mock_client)

        assert isinstance(result, dict)
        assert result["user_id"] == "user-123"
        assert result["display_name"] == "Integration Test User"
        assert result["given_name"] == "Integration"
        assert result["surname"] == "User"
        assert result["user_principal_name"] == "integration.user@contoso.com"
        assert result["mail"] == "integration.user@contoso.com"
        assert result["job_title"] == "Test Engineer"
        assert result["department"] == "QA"
        assert result["office_location"] == "Remote"
        assert result["business_phones"] == ["+1-555-TEST"]
        assert result["mobile_phone"] == "+1-555-MOBILE"
        assert result["preferred_language"] == "en-US"
        assert result["account_enabled"] is True
        assert result["tenant_domain"] == "contoso.com"
        assert result["teams_access"] is True
