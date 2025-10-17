from typing import Any, TypedDict, cast

from slack_sdk.web.async_client import AsyncWebClient


class WhoAmIResponse(TypedDict, total=False):
    user_id: str
    username: str
    display_name: str
    real_name: str
    email: str
    profile_picture_url: str
    title: str
    phone: str
    first_name: str
    last_name: str
    pronouns: str
    status_text: str
    status_emoji: str
    slack_access: bool


async def build_who_am_i_response(context: Any, slack_client: AsyncWebClient) -> WhoAmIResponse:
    """Build complete who_am_i response from Slack APIs."""
    auth_token = context.get_auth_token_or_empty()

    auth_info = await _get_auth_info(slack_client)

    user_profile = await _get_user_profile(auth_token, auth_info["user_id"])

    user_info: dict[str, Any] = {}
    user_info.update(_extract_auth_info(auth_info))
    user_info.update(_extract_user_profile(user_profile))

    return cast(WhoAmIResponse, user_info)


async def _get_auth_info(slack_client: AsyncWebClient) -> dict[str, Any]:
    """Get authentication information including user_id and team info."""
    response = await slack_client.auth_test()
    return cast(dict[str, Any], response.data)


async def _get_user_profile(auth_token: str, user_id: str) -> dict[str, Any]:
    """Get detailed user profile information."""
    slack_client = AsyncWebClient(token=auth_token)
    response = await slack_client.users_info(user=user_id)
    response_dict = cast(dict[str, Any], response)
    if not response_dict.get("ok"):
        error = response_dict.get("error", "Unknown error")
        raise RuntimeError(f"Failed to get user info: {error}")
    return cast(dict[str, Any], response_dict["user"])


def _extract_auth_info(auth_info: dict[str, Any]) -> dict[str, Any]:
    """Extract authentication information."""
    extracted = {}

    if auth_info.get("user_id"):
        extracted["user_id"] = auth_info["user_id"]
    if auth_info.get("user"):
        extracted["username"] = auth_info["user"]

    extracted["slack_access"] = bool(auth_info.get("ok"))

    return extracted


def _extract_user_profile(user_profile: dict[str, Any]) -> dict[str, Any]:
    """Extract user profile information."""
    extracted = {}

    if user_profile.get("real_name"):
        extracted["real_name"] = user_profile["real_name"]
    if user_profile.get("name"):
        extracted["username"] = user_profile["name"]

    profile = user_profile.get("profile", {})
    extracted.update(_extract_profile_fields(profile))
    extracted.update(_extract_profile_picture(profile))

    return extracted


def _extract_profile_fields(profile: dict[str, Any]) -> dict[str, Any]:
    """Extract profile fields from user profile."""
    extracted = {}

    fields = [
        ("display_name", "display_name"),
        ("real_name", "real_name"),
        ("email", "email"),
        ("title", "title"),
        ("phone", "phone"),
        ("first_name", "first_name"),
        ("last_name", "last_name"),
        ("pronouns", "pronouns"),
        ("status_text", "status_text"),
        ("status_emoji", "status_emoji"),
    ]

    for profile_key, extracted_key in fields:
        if profile.get(profile_key):
            extracted[extracted_key] = profile[profile_key]

    return extracted


def _extract_profile_picture(profile: dict[str, Any]) -> dict[str, Any]:
    """Extract profile picture URL from user profile."""
    for size in [
        "image_1024",
        "image_512",
        "image_192",
        "image_72",
        "image_48",
        "image_32",
        "image_24",
    ]:
        if profile.get(size):
            return {"profile_picture_url": profile[size]}
    return {}
