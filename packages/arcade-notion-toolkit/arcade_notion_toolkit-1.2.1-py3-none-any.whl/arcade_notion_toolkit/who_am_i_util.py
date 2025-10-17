from typing import Any, TypedDict

import httpx
from arcade_tdk import ToolContext

from arcade_notion_toolkit.utils import get_headers, get_url


class WhoAmIResponse(TypedDict, total=False):
    user_id: str
    user_name: str
    user_type: str
    avatar_url: str
    owner_user_id: str
    owner_user_name: str
    owner_user_type: str
    owner_avatar_url: str
    workspace_name: str
    workspace_id: str
    workspace_domain: str
    notion_access: bool


async def build_who_am_i_response(context: ToolContext) -> WhoAmIResponse:
    """Build complete who_am_i response from Notion APIs."""

    user_info = await _get_current_user_info(context)
    workspace_info = await _get_basic_workspace_info(context)

    response_data = {}
    response_data.update(_extract_user_info(user_info))
    response_data.update(_extract_basic_workspace_info(workspace_info))
    response_data["notion_access"] = True

    return response_data  # type: ignore[return-value]


async def _get_basic_workspace_info(context: ToolContext) -> dict[str, Any]:
    """Get basic workspace information with a simple search call."""
    headers = get_headers(context)
    url = get_url("search_by_title")

    payload = {
        "page_size": 1,
        "sort": {"direction": "descending", "timestamp": "last_edited_time"},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        return {
            "results": data.get("results", []),
            "has_more": data.get("has_more", False),
        }


async def _get_current_user_info(context: ToolContext) -> dict[str, Any]:
    """Get current user/bot information from Notion API."""
    headers = get_headers(context)
    url = get_url("get_current_user")

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        return data  # type: ignore[no-any-return]


def _extract_user_info(user_info: dict[str, Any]) -> dict[str, Any]:
    """Extract user information from Notion user API response."""
    extracted = {}

    extracted.update(_extract_basic_user_fields(user_info))
    extracted.update(_extract_owner_info(user_info))

    return extracted


def _extract_basic_user_fields(user_info: dict[str, Any]) -> dict[str, Any]:
    """Extract basic user fields from user info."""
    fields = {}

    if user_info.get("id"):
        fields["user_id"] = user_info["id"]
    if user_info.get("name"):
        fields["user_name"] = user_info["name"]
    if user_info.get("type"):
        fields["user_type"] = user_info["type"]
    if user_info.get("avatar_url"):
        fields["avatar_url"] = user_info["avatar_url"]

    return fields


def _extract_owner_info(user_info: dict[str, Any]) -> dict[str, Any]:
    """Extract owner information if this is a bot."""
    owner_fields: dict[str, Any] = {}

    bot_info = user_info.get("bot")
    if not bot_info:
        return owner_fields

    owner = bot_info.get("owner")
    if not owner:
        return owner_fields

    owner_user = owner.get("user")
    if not owner_user:
        return owner_fields

    if owner_user.get("id"):
        owner_fields["owner_user_id"] = owner_user["id"]
    if owner_user.get("name"):
        owner_fields["owner_user_name"] = owner_user["name"]
    if owner_user.get("type"):
        owner_fields["owner_user_type"] = owner_user["type"]
    if owner_user.get("avatar_url"):
        owner_fields["owner_avatar_url"] = owner_user["avatar_url"]

    return owner_fields


def _extract_basic_workspace_info(workspace_info: dict[str, Any]) -> dict[str, Any]:
    """Extract basic workspace information without statistics."""
    extracted = {}

    results = workspace_info.get("results", [])
    if results:
        first_result = results[0]

        if first_result.get("parent"):
            parent = first_result["parent"]
            if parent.get("type") == "workspace":
                extracted["workspace_name"] = "Notion Workspace"
                extracted["workspace_id"] = "workspace"

        if first_result.get("url"):
            url = first_result["url"]
            if "notion.so" in url:
                parts = url.split("/")
                if len(parts) > 2:
                    domain_part = parts[2]
                    if domain_part != "www.notion.so":
                        extracted["workspace_domain"] = domain_part

    if "workspace_name" not in extracted:
        extracted["workspace_name"] = "Notion Workspace"
    if "workspace_id" not in extracted:
        extracted["workspace_id"] = "workspace"

    return extracted
