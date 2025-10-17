from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Notion

from arcade_notion_toolkit.who_am_i_util import build_who_am_i_response


@tool(requires_auth=Notion())
async def who_am_i(
    context: ToolContext,
) -> Annotated[
    dict[str, Any],
    "Get comprehensive user profile and Notion workspace information.",
]:
    """
    Get information about the current user and their Notion workspace.

    This tool provides detailed information about the authenticated user's
    Notion workspace including workspace statistics, user context, and
    integration details.
    """
    user_info = await build_who_am_i_response(context)
    return dict(user_info)
