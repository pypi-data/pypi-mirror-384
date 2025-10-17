from typing import Any, TypedDict, cast

from msgraph import GraphServiceClient

from arcade_outlook_calendar._utils import get_default_calendar_timezone


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
    default_timezone: str
    mailbox_timezone: str
    calendar_count: int
    primary_calendar_id: str
    primary_calendar_name: str
    primary_calendar_timezone: str
    calendar_access_role: str
    outlook_calendar_access: bool


async def build_who_am_i_response(client: GraphServiceClient) -> WhoAmIResponse:
    """Build complete who_am_i response from Microsoft Graph APIs."""

    # Get current user info, calendar info, and timezone info
    user_info = await _get_current_user(client)
    calendar_info = await _get_calendar_info(client)
    timezone_info = await _get_timezone_info(client)

    # Build response
    response_data: dict[str, Any] = {}
    response_data.update(_extract_user_info(user_info))
    response_data.update(_extract_calendar_info(calendar_info))
    response_data.update(_extract_timezone_info(timezone_info))

    return cast(WhoAmIResponse, response_data)


async def _get_current_user(client: GraphServiceClient) -> dict[str, Any]:
    """Get current user information from Microsoft Graph API."""
    response = await client.me.get()

    if not response:
        return {}

    user_data = _extract_basic_user_fields(response)
    user_data.update(_extract_contact_fields(response))
    user_data.update(_extract_org_fields(response))
    user_data.update(_extract_tenant_domain(user_data))

    return user_data


def _extract_basic_user_fields(response: Any) -> dict[str, Any]:
    """Extract basic user fields from Microsoft Graph response."""
    user_data = {}

    if hasattr(response, "id") and response.id:
        user_data["id"] = response.id
    if hasattr(response, "display_name") and response.display_name:
        user_data["display_name"] = response.display_name
    if hasattr(response, "given_name") and response.given_name:
        user_data["given_name"] = response.given_name
    if hasattr(response, "surname") and response.surname:
        user_data["surname"] = response.surname
    if hasattr(response, "user_principal_name") and response.user_principal_name:
        user_data["user_principal_name"] = response.user_principal_name
    if hasattr(response, "mail") and response.mail:
        user_data["mail"] = response.mail
    if hasattr(response, "preferred_language") and response.preferred_language:
        user_data["preferred_language"] = response.preferred_language
    if hasattr(response, "account_enabled") and response.account_enabled is not None:
        user_data["account_enabled"] = response.account_enabled

    return user_data


def _extract_contact_fields(response: Any) -> dict[str, Any]:
    """Extract contact fields from Microsoft Graph response."""
    contact_data = {}

    if hasattr(response, "business_phones") and response.business_phones:
        contact_data["business_phones"] = list(response.business_phones)
    if hasattr(response, "mobile_phone") and response.mobile_phone:
        contact_data["mobile_phone"] = response.mobile_phone

    return contact_data


def _extract_org_fields(response: Any) -> dict[str, Any]:
    """Extract organization fields from Microsoft Graph response."""
    org_data = {}

    if hasattr(response, "job_title") and response.job_title:
        org_data["job_title"] = response.job_title
    if hasattr(response, "department") and response.department:
        org_data["department"] = response.department
    if hasattr(response, "office_location") and response.office_location:
        org_data["office_location"] = response.office_location

    return org_data


def _extract_tenant_domain(user_data: dict[str, Any]) -> dict[str, Any]:
    """Extract tenant domain from user principal name."""
    tenant_data = {}

    if user_data.get("user_principal_name"):
        upn = user_data["user_principal_name"]
        if "@" in upn:
            domain = upn.split("@")[1]
            if domain:
                tenant_data["tenant_domain"] = domain

    return tenant_data


async def _get_calendar_info(client: GraphServiceClient) -> dict[str, Any]:
    """Get calendar information from Microsoft Graph API."""
    # Get calendars
    calendars_response = await client.me.calendars.get()

    calendar_data: dict[str, Any] = {
        "calendar_count": 0,
        "primary_calendar_id": None,
        "primary_calendar_name": None,
        "primary_calendar_timezone": None,
        "calendar_access_role": None,
    }

    if calendars_response and calendars_response.value:
        calendar_data["calendar_count"] = len(calendars_response.value)

        # Find primary calendar
        for calendar in calendars_response.value:
            if hasattr(calendar, "is_default_calendar") and calendar.is_default_calendar:
                if hasattr(calendar, "id") and calendar.id:
                    calendar_data["primary_calendar_id"] = calendar.id
                if hasattr(calendar, "name") and calendar.name:
                    calendar_data["primary_calendar_name"] = calendar.name
                if hasattr(calendar, "time_zone") and calendar.time_zone:
                    calendar_data["primary_calendar_timezone"] = calendar.time_zone
                if hasattr(calendar, "can_edit") and calendar.can_edit is not None:
                    calendar_data["calendar_access_role"] = (
                        "Owner" if calendar.can_edit else "Reader"
                    )
                break

    return calendar_data


async def _get_timezone_info(client: GraphServiceClient) -> dict[str, Any]:
    """Get timezone information from Microsoft Graph API."""
    timezone_data: dict[str, Any] = {
        "default_timezone": None,
        "mailbox_timezone": None,
    }

    # Get default calendar timezone using the utility function
    default_timezone = await get_default_calendar_timezone(client)
    if default_timezone:
        timezone_data["default_timezone"] = default_timezone

    # Get mailbox timezone from mailbox settings
    mailbox_response = await client.me.mailbox_settings.get()
    if mailbox_response and hasattr(mailbox_response, "time_zone") and mailbox_response.time_zone:
        timezone_data["mailbox_timezone"] = mailbox_response.time_zone

    return timezone_data


def _extract_user_info(user_info: dict[str, Any]) -> dict[str, Any]:
    """Extract user information from Microsoft Graph user API response."""
    extracted: dict[str, Any] = {}

    def copy_field(src_key: str, dest_key: str | None = None) -> None:
        value = user_info.get(src_key)
        if value is not None:
            extracted[dest_key or src_key] = value

    # Identification
    copy_field("id", "user_id")
    copy_field("display_name")
    copy_field("given_name")
    copy_field("surname")
    copy_field("user_principal_name")
    copy_field("mail")

    # Organization
    copy_field("job_title")
    copy_field("department")
    copy_field("office_location")

    # Contact
    copy_field("business_phones")
    copy_field("mobile_phone")

    # Settings
    copy_field("preferred_language")
    # account_enabled can be False, so handle presence explicitly
    if "account_enabled" in user_info:
        extracted["account_enabled"] = user_info["account_enabled"]
    copy_field("tenant_domain")

    return extracted


def _extract_calendar_info(calendar_info: dict[str, Any]) -> dict[str, Any]:
    """Extract calendar information from Microsoft Graph calendars API response."""
    extracted = {}

    # Calendar information
    if calendar_info.get("calendar_count") is not None:
        extracted["calendar_count"] = calendar_info["calendar_count"]
    if calendar_info.get("primary_calendar_id"):
        extracted["primary_calendar_id"] = calendar_info["primary_calendar_id"]
    if calendar_info.get("primary_calendar_name"):
        extracted["primary_calendar_name"] = calendar_info["primary_calendar_name"]
    if calendar_info.get("primary_calendar_timezone"):
        extracted["primary_calendar_timezone"] = calendar_info["primary_calendar_timezone"]
    if calendar_info.get("calendar_access_role"):
        extracted["calendar_access_role"] = calendar_info["calendar_access_role"]

    extracted["outlook_calendar_access"] = True

    return extracted


def _extract_timezone_info(timezone_info: dict[str, Any]) -> dict[str, Any]:
    """Extract timezone information from Microsoft Graph API response."""
    extracted = {}

    # Timezone information
    if timezone_info.get("default_timezone"):
        extracted["default_timezone"] = timezone_info["default_timezone"]
    if timezone_info.get("mailbox_timezone"):
        extracted["mailbox_timezone"] = timezone_info["mailbox_timezone"]

    return extracted
