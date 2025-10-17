from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Microsoft

from arcade_outlook_mail.client import get_client
from arcade_outlook_mail.who_am_i_util import build_who_am_i_response


@tool(requires_auth=Microsoft(scopes=["User.Read", "Mail.Read"]))
async def who_am_i(
    context: ToolContext,
) -> Annotated[
    dict[str, Any],
    "Get comprehensive user profile and Outlook Mail environment information.",
]:
    """
    Get comprehensive user profile and Outlook Mail environment information.

    This tool provides detailed information about the authenticated user including
    their name, email, mailbox settings, automatic replies configuration, and other
    important profile details from Outlook Mail services.
    """

    client = get_client(context.get_auth_token_or_empty())
    user_info = await build_who_am_i_response(client)

    return dict(user_info)
