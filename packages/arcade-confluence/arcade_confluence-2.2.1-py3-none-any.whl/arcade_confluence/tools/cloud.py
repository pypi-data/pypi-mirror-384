from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Atlassian

from arcade_confluence.utils import get_atlassian_clouds


# Note: The read:page:confluence scope is required to run a dummy API check to
# determine whether the auth token is authorized for a given Atlassian Cloud.
@tool(requires_auth=Atlassian(scopes=["read:page:confluence"]))
async def get_available_atlassian_clouds(
    context: ToolContext,
) -> Annotated[dict[str, dict[str, Any]], "Available Atlassian Clouds"]:
    """Get available Atlassian Clouds."""
    return {"clouds": await get_atlassian_clouds(context)}
