from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Atlassian
from arcade_tdk.errors import ToolExecutionError

from arcade_confluence import system_context_utils


@tool(
    requires_auth=Atlassian(
        scopes=[
            "read:content-details:confluence",  # /user/current endpoint, accessible-resources API
            "read:page:confluence",  # Required by resolve_cloud_id function
        ]
    )
)
async def who_am_i(
    context: ToolContext,
) -> Annotated[
    dict[str, Any],
    "Dictionary containing the current user's information and their available Atlassian Clouds.",
]:
    """
    CALL THIS TOOL FIRST to establish user profile context.

    Get information about the currently logged-in user and their available Confluence clouds.
    """
    (
        clouds_available,
        current_user,
    ) = await system_context_utils.get_available_clouds_and_user_info(context)

    if not clouds_available:
        msg = "No authorized Atlassian clouds found for the current user."
        raise ToolExecutionError(msg)

    return system_context_utils.create_user_context_response(current_user, clouds_available)
