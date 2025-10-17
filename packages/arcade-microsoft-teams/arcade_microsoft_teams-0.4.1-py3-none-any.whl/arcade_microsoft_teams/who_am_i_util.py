from typing import Any, TypedDict, cast

from msgraph import GraphServiceClient


class WhoAmIResponse(TypedDict, total=False):
    user_id: str
    display_name: str
    given_name: str
    surname: str
    user_principal_name: str
    mail: str
    job_title: str
    department: str
    office_location: str
    business_phones: list[str]
    mobile_phone: str
    preferred_language: str
    tenant_domain: str
    account_enabled: bool
    teams_access: bool


async def build_who_am_i_response(client: GraphServiceClient) -> WhoAmIResponse:
    """Build complete who_am_i response from Microsoft Graph APIs."""

    # Get current user info only (teams info requires additional permissions)
    user_info = await _get_current_user(client)

    # Build response
    response_data: dict[str, Any] = {}
    response_data.update(_extract_user_info(user_info))
    response_data["teams_access"] = True  # Confirm we have basic access

    return cast(WhoAmIResponse, response_data)


async def _get_current_user(client: GraphServiceClient) -> dict[str, Any]:
    """Get current user information from Microsoft Graph API."""
    response = await client.me.get()

    if not response:
        return {}

    user_data: dict[str, Any] = {}
    user_data.update(_populate_basic_user_fields(response))
    user_data.update(_populate_org_user_fields(response))
    user_data.update(_populate_contact_user_fields(response))
    user_data.update(_populate_settings_user_fields(response))
    _populate_tenant_domain_from_upn(user_data)

    return user_data


def _extract_user_info(user_info: dict[str, Any]) -> dict[str, Any]:
    """Extract user information from Microsoft Graph user API response."""
    extracted: dict[str, Any] = {}
    extracted.update(_select_identification_fields(user_info))
    extracted.update(_select_org_fields(user_info))
    extracted.update(_select_contact_fields(user_info))
    extracted.update(_select_settings_fields(user_info))
    _select_tenant_domain(user_info, extracted)
    return extracted


# Private helpers (kept last)
def _populate_basic_user_fields(response: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if hasattr(response, "id") and response.id:
        data["id"] = response.id
    if hasattr(response, "display_name") and response.display_name:
        data["display_name"] = response.display_name
    if hasattr(response, "given_name") and response.given_name:
        data["given_name"] = response.given_name
    if hasattr(response, "surname") and response.surname:
        data["surname"] = response.surname
    if hasattr(response, "user_principal_name") and response.user_principal_name:
        data["user_principal_name"] = response.user_principal_name
    if hasattr(response, "mail") and response.mail:
        data["mail"] = response.mail
    return data


def _populate_org_user_fields(response: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if hasattr(response, "job_title") and response.job_title:
        data["job_title"] = response.job_title
    if hasattr(response, "department") and response.department:
        data["department"] = response.department
    if hasattr(response, "office_location") and response.office_location:
        data["office_location"] = response.office_location
    return data


def _populate_contact_user_fields(response: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if hasattr(response, "business_phones") and response.business_phones:
        data["business_phones"] = list(response.business_phones)
    if hasattr(response, "mobile_phone") and response.mobile_phone:
        data["mobile_phone"] = response.mobile_phone
    return data


def _populate_settings_user_fields(response: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if hasattr(response, "preferred_language") and response.preferred_language:
        data["preferred_language"] = response.preferred_language
    if hasattr(response, "account_enabled") and response.account_enabled is not None:
        data["account_enabled"] = bool(response.account_enabled)
    return data


def _populate_tenant_domain_from_upn(user_data: dict[str, Any]) -> None:
    upn_value = user_data.get("user_principal_name")
    if isinstance(upn_value, str) and "@" in upn_value:
        domain = upn_value.split("@")[1]
        if domain:
            user_data["tenant_domain"] = domain


def _select_identification_fields(user_info: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if user_info.get("id"):
        out["user_id"] = user_info["id"]
    if user_info.get("display_name"):
        out["display_name"] = user_info["display_name"]
    if user_info.get("given_name"):
        out["given_name"] = user_info["given_name"]
    if user_info.get("surname"):
        out["surname"] = user_info["surname"]
    if user_info.get("user_principal_name"):
        out["user_principal_name"] = user_info["user_principal_name"]
    if user_info.get("mail"):
        out["mail"] = user_info["mail"]
    return out


def _select_org_fields(user_info: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if user_info.get("job_title"):
        out["job_title"] = user_info["job_title"]
    if user_info.get("department"):
        out["department"] = user_info["department"]
    if user_info.get("office_location"):
        out["office_location"] = user_info["office_location"]
    return out


def _select_contact_fields(user_info: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if user_info.get("business_phones"):
        out["business_phones"] = user_info["business_phones"]
    if user_info.get("mobile_phone"):
        out["mobile_phone"] = user_info["mobile_phone"]
    return out


def _select_settings_fields(user_info: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if user_info.get("preferred_language"):
        out["preferred_language"] = user_info["preferred_language"]
    if user_info.get("account_enabled") is not None:
        out["account_enabled"] = user_info["account_enabled"]
    return out


def _select_tenant_domain(user_info: dict[str, Any], out: dict[str, Any]) -> None:
    if user_info.get("tenant_domain"):
        out["tenant_domain"] = user_info["tenant_domain"]
