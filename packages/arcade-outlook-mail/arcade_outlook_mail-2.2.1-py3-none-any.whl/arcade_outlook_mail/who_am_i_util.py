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
    primary_email: str
    outlook_mail_access: bool


async def build_who_am_i_response(client: GraphServiceClient) -> WhoAmIResponse:
    """Build complete who_am_i response from Microsoft Graph APIs."""

    # Get current user info and mailbox settings
    user_info = await _get_current_user(client)
    mailbox_settings = await _get_mailbox_settings(client)

    # Build response
    response_data: dict[str, Any] = {}
    response_data.update(_extract_user_info(user_info))
    response_data.update(_extract_mailbox_settings(mailbox_settings))

    return cast(WhoAmIResponse, response_data)


async def _get_current_user(client: GraphServiceClient) -> dict[str, Any]:
    """Get current user information from Microsoft Graph API."""
    response = await client.me.get()

    # Convert the response to a dictionary-like format
    user_data = {}
    if response:
        user_data["id"] = getattr(response, "id", None)
        user_data["display_name"] = getattr(response, "display_name", None)
        user_data["given_name"] = getattr(response, "given_name", None)
        user_data["surname"] = getattr(response, "surname", None)
        user_data["user_principal_name"] = getattr(response, "user_principal_name", None)
        user_data["mail"] = getattr(response, "mail", None)
        user_data["job_title"] = getattr(response, "job_title", None)
        user_data["department"] = getattr(response, "department", None)
        user_data["office_location"] = getattr(response, "office_location", None)
        user_data["business_phones"] = getattr(response, "business_phones", None)
        user_data["mobile_phone"] = getattr(response, "mobile_phone", None)
        user_data["preferred_language"] = getattr(response, "preferred_language", None)
        user_data["account_enabled"] = getattr(response, "account_enabled", None)

        # Extract tenant domain from user principal name if available
        upn_value = user_data.get("user_principal_name")
        if isinstance(upn_value, str) and "@" in upn_value:
            domain = upn_value.split("@")[1]
            user_data["tenant_domain"] = domain

    return user_data


async def _get_mailbox_settings(client: GraphServiceClient) -> dict[str, Any]:
    """Get mailbox settings from Microsoft Graph API."""
    try:
        response = await client.me.get()

        mailbox_data: dict[str, Any] = {}
        if response and getattr(response, "mail", None):
            mailbox_data["primary_email"] = response.mail
    except Exception:
        # If any mail info is not accessible, return empty dict
        return {}
    else:
        return mailbox_data


def _extract_user_info(user_info: dict[str, Any]) -> dict[str, Any]:
    """Extract user information from Microsoft Graph user API response."""
    extracted: dict[str, Any] = {}

    extracted.update(_extract_basic_user_fields(user_info))
    extracted.update(_extract_job_and_org_fields(user_info))
    extracted.update(_extract_contact_fields(user_info))
    extracted.update(_extract_preferences_fields(user_info))
    extracted.update(_extract_tenant_fields(user_info))

    return extracted


def _extract_basic_user_fields(user_info: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if user_info.get("id"):
        fields["user_id"] = user_info["id"]
    if user_info.get("display_name"):
        fields["display_name"] = user_info["display_name"]
    if user_info.get("given_name"):
        fields["given_name"] = user_info["given_name"]
    if user_info.get("surname"):
        fields["surname"] = user_info["surname"]
    if user_info.get("user_principal_name"):
        fields["user_principal_name"] = user_info["user_principal_name"]
    if user_info.get("mail"):
        fields["mail"] = user_info["mail"]
    return fields


def _extract_job_and_org_fields(user_info: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if user_info.get("job_title"):
        fields["job_title"] = user_info["job_title"]
    if user_info.get("department"):
        fields["department"] = user_info["department"]
    if user_info.get("office_location"):
        fields["office_location"] = user_info["office_location"]
    return fields


def _extract_contact_fields(user_info: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if user_info.get("business_phones"):
        fields["business_phones"] = user_info["business_phones"]
    if user_info.get("mobile_phone"):
        fields["mobile_phone"] = user_info["mobile_phone"]
    return fields


def _extract_preferences_fields(user_info: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if user_info.get("preferred_language"):
        fields["preferred_language"] = user_info["preferred_language"]
    if user_info.get("account_enabled") is not None:
        fields["account_enabled"] = user_info["account_enabled"]
    return fields


def _extract_tenant_fields(user_info: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if user_info.get("tenant_domain"):
        fields["tenant_domain"] = user_info["tenant_domain"]
    return fields


def _extract_mailbox_settings(mailbox_settings: dict[str, Any]) -> dict[str, Any]:
    """Extract mailbox settings from Microsoft Graph API response."""
    extracted = {}

    # Primary email
    if mailbox_settings.get("primary_email"):
        extracted["primary_email"] = mailbox_settings["primary_email"]

    extracted["outlook_mail_access"] = True

    return extracted
