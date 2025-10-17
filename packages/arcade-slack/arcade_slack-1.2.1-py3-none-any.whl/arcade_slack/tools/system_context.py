from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Slack
from slack_sdk.web.async_client import AsyncWebClient

from arcade_slack.who_am_i_util import build_who_am_i_response


@tool(
    requires_auth=Slack(
        scopes=[
            "users:read",
            "users:read.email",
        ]
    )
)
async def who_am_i(
    context: ToolContext,
) -> Annotated[
    dict[str, Any],
    "Get comprehensive user profile and Slack information.",
]:
    """
    Get comprehensive user profile and Slack information.

    This tool provides detailed information about the authenticated user including
    their name, email, profile picture, and other important profile details from
    Slack services.
    """

    auth_token = context.get_auth_token_or_empty()
    slack_client = AsyncWebClient(token=auth_token)
    user_info = await build_who_am_i_response(context, slack_client)

    return dict(user_info)
