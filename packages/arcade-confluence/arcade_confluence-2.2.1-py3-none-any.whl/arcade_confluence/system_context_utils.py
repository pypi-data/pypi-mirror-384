"""Utility functions for system context operations."""

from typing import Any

from arcade_tdk import ToolContext

from arcade_confluence.client import ConfluenceClientV1
from arcade_confluence.tools.cloud import get_available_atlassian_clouds
from arcade_confluence.utils import clean_user_dict


async def get_available_clouds_and_user_info(
    context: ToolContext,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """
    Get available Atlassian clouds and current user information.

    Args:
        context: Tool context for authentication

    Returns:
        Tuple of (clouds_available, current_user_info)
    """
    cloud_response = await get_available_atlassian_clouds(context)
    clouds_available = cloud_response.get("clouds", {}).get("clouds_available", [])

    current_user = None
    if clouds_available:
        # Get user info from the first available cloud
        first_cloud = clouds_available[0]
        current_user = await get_current_user_info(
            context,
            first_cloud["atlassian_cloud_id"],
            first_cloud["atlassian_cloud_name"],
        )

    return clouds_available, current_user


async def get_current_user_info(
    context: ToolContext, cloud_id: str, cloud_name: str
) -> dict[str, Any]:
    """
    Retrieve current user information from a specific Confluence cloud.

    Args:
        context: Tool context for authentication
        cloud_id: Atlassian cloud ID
        cloud_name: Atlassian cloud name

    Returns:
        Dictionary containing cleaned user information.
    """
    client = ConfluenceClientV1(token=context.get_auth_token_or_empty(), cloud_id=cloud_id)
    # Confluence API v1 uses /user/current endpoint to get current user information
    user_response = await client.get("user/current")
    return clean_user_dict(user_response, cloud_name)


def create_user_context_response(
    current_user: dict[str, Any] | None,
    clouds_available: list[dict[str, Any]],
    error: str | None = None,
) -> dict[str, Any]:
    """
    Create a standardized response for user context operations.

    Args:
        current_user: User information dictionary or None
        clouds_available: List of available cloud dictionaries
        error: Error message if any

    Returns:
        Dictionary containing user context response.
    """
    if error:
        return {
            "error": error,
            "clouds_available": clouds_available,
        }

    return {
        "current_user": current_user,
        "clouds_available": clouds_available,
    }
