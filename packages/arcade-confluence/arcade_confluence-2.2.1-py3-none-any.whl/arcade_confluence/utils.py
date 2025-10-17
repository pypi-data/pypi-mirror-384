import asyncio
import json
import re
import uuid
from typing import Any, cast

import httpx
from arcade_tdk import ToolContext
from arcade_tdk.errors import RetryableToolError, ToolExecutionError


def remove_none_values(data: dict) -> dict:
    """Remove all keys with None values from the dictionary."""
    return {k: v for k, v in data.items() if v is not None}


def validate_ids(ids: list[str] | None, max_length: int) -> None:
    """Validate a list of IDs. The ids can be page ids, space ids, etc.

    A valid id is a string that is a number.

    Args:
        ids: A list of IDs to validate.

    Returns:
        None

    Raises:
        ToolExecutionError: If any of the IDs are not valid.
        RetryableToolError: If the number of IDs is greater than the max length.
    """
    if not ids:
        return
    if len(ids) > max_length:
        raise RetryableToolError(
            message=f"The 'ids' parameter must have less than {max_length} items. Got {len(ids)}"
        )
    if any(not id_.isdigit() for id_ in ids):
        raise ToolExecutionError(message="Invalid ID provided. IDs are numeric")


def build_child_url(base_url: str, child: dict) -> str | None:
    """Build URL for a child node based on its type and status.

    Args:
        base_url: The base URL for the Confluence space
        child: A dictionary representing a Confluence content item

    Returns:
        The URL for the child, or None if it can't be determined
    """
    if child["type"] in ("whiteboard", "database", "embed"):
        return f"{base_url}/{child['type']}/{child['id']}"
    elif child["type"] == "folder":
        return None
    elif child["type"] == "page":
        parsed_title = re.sub(r"[ '\s]+", "+", child["title"].strip())
        if child.get("status") == "draft":
            return f"{base_url}/{child['type']}s/edit-v2/{child['id']}"
        else:
            return f"{base_url}/{child['type']}s/{child['id']}/{parsed_title}"
    return None


def build_hierarchy(transformed_children: list, parent_id: str, parent_node: dict) -> None:
    """Build parent-child hierarchy from a flat list of descendants.

    This function takes a flat list of items that have parent_id references and
    builds a hierarchical tree structure. It modifies the parent_node in place.

    Args:
        transformed_children: List of child nodes with parent_id fields
        parent_id: The ID of the parent node
        parent_node: The parent node to attach direct children to

    Returns:
        None (modifies parent_node in place)
    """
    # Create a map of children by their ID for efficient lookups
    child_map = {child["id"]: child for child in transformed_children}

    # Find all direct children of the given parent_id
    direct_children = []
    for child in transformed_children:
        if child.get("parent_id") == parent_id:
            direct_children.append(child)
        elif child.get("parent_id") in child_map:
            # Add child to its parent's children list
            parent = child_map[child.get("parent_id")]
            if "children" not in parent:
                parent["children"] = []
            parent["children"].append(child)

    # Set the direct children on the parent node
    parent_node["children"] = direct_children


async def get_atlassian_clouds(context: ToolContext) -> dict[str, list]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.atlassian.com/oauth/token/accessible-resources",
            headers={"Authorization": f"Bearer {context.get_auth_token_or_empty()}"},
        )

    verified_clouds = response.json()
    cloud_ids_seen = set()
    unique_clouds = []

    for cloud in verified_clouds:
        if cloud["id"] not in cloud_ids_seen:
            unique_clouds.append({
                "atlassian_cloud_id": cloud["id"],
                "atlassian_cloud_name": cloud["name"],
                "atlassian_cloud_url": cloud["url"],
            })
            cloud_ids_seen.add(cloud["id"])

    semaphore = asyncio.Semaphore(3)

    verified_clouds = await asyncio.gather(*[
        check_if_cloud_is_authorized(context, cloud, semaphore) for cloud in unique_clouds
    ])

    return {
        "clouds_available": [
            cloud_available for cloud_available in verified_clouds if cloud_available is not False
        ]
    }


async def resolve_cloud_id(context: ToolContext, cloud_id: str | None) -> str:
    try:
        uuid.UUID(cloud_id)
    except (AttributeError, TypeError, ValueError):
        is_valid_uuid = False
    else:
        is_valid_uuid = True

    # If this is already a valid Cloud ID, return it
    if is_valid_uuid:
        return cast(str, cloud_id)

    # If not, it's possibly a Cloud name, so we try to match that.
    if isinstance(cloud_id, str) and cloud_id != "":
        return await get_cloud_id_by_cloud_name(context, cloud_name=cloud_id)

    # As a last resort, try to get a unique Cloud ID from the available Atlassian Clouds
    return await get_unique_cloud_id(context)


async def get_cloud_id_by_cloud_name(context: ToolContext, cloud_name: str) -> str:
    response = await get_atlassian_clouds(context)
    clouds = response["clouds_available"]

    for cloud in clouds:
        if (
            # Case-insensitive match in case of cloud names.
            cloud["atlassian_cloud_name"].casefold() == cloud_name.casefold()
            # Match the ID as well just in case. Who knows, Atlassian may start
            # using some weird values as cloud IDs. If the value provided matches
            # an ID in the list of clouds, then it's a match.
            or cloud["atlassian_cloud_id"] == cloud_name
        ):
            return cast(str, cloud["atlassian_cloud_id"])

    message = f"No Atlassian Cloud found matching '{cloud_name}'"
    available_clouds_str = f"Available Atlassian Clouds:\n\n```json\n{json.dumps(clouds)}\n```"

    raise RetryableToolError(
        message=message,
        developer_message=message,
        additional_prompt_content=available_clouds_str,
    )


async def get_unique_cloud_id(context: ToolContext) -> str:
    response = await get_atlassian_clouds(context)
    clouds = response["clouds_available"]

    if len(clouds) == 0:
        message = "No Atlassian Cloud is available. Please authorize an Atlassian Cloud."
        raise ToolExecutionError(
            message=message,
            developer_message=message,
        )

    if len(clouds) > 1:
        message = (
            "Multiple Atlassian Clouds are available. One Cloud ID has to be selected and provided "
            "in the tool call using the `atlassian_cloud_id` argument."
        )
        raise RetryableToolError(
            message=message,
            developer_message=message,
            additional_prompt_content=(
                f"Available Atlassian Clouds:\n\n```json\n{json.dumps(clouds)}\n```"
            ),
        )

    return cast(str, clouds[0]["atlassian_cloud_id"])


async def check_if_cloud_is_authorized(
    context: ToolContext,
    cloud: dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> dict[str, Any] | bool:
    """Confirm whether an Atlassian Cloud is authorized for the current auth token.

    The Atlassian available-resources endpoint may return Clouds that have not been
    authorized by the current user. This is a known Atlassian OAuth2 API bug [1].

    We run this check against the '/pages' endpoint to confirm whether the Cloud
    was actually authorized for the current auth token.

    [1] Reference about the Atlassian API bug:
    https://community.developer.atlassian.com/t/urgent-api-accessible-resources-endpoint-returns-sites-resources-that-are-not-permitted-by-the-user/66899
    Archived (2025-07-22): https://archive.is/0noNX
    """
    cloud_id = cloud["atlassian_cloud_id"]

    async with semaphore, httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.atlassian.com/ex/confluence/{cloud_id}/wiki/api/v2/pages",
            headers={"Authorization": f"Bearer {context.get_auth_token_or_empty()}"},
        )

    if response.status_code == 200:
        return cloud

    elif response.status_code == 429 or response.status_code >= 500:
        response.raise_for_status()

    else:
        return False

    return False


def clean_user_dict(user: dict, cloud_name: str | None = None) -> dict:
    """Clean and standardize user information from Confluence API response."""
    data = {
        "id": user.get("accountId") or user.get("userKey"),
        "name": user.get("displayName") or user.get("username"),
        "active": user.get("active", True),
    }

    if user.get("email"):
        data["email"] = user["email"]

    if user.get("accountType"):
        data["account_type"] = user["accountType"]

    if user.get("timeZone"):
        data["timezone"] = user["timeZone"]

    # Add confluence_gui_url field if cloud_name is provided
    if cloud_name:
        account_id = user.get("accountId") or user.get("userKey")
        if account_id:
            data["confluence_gui_url"] = build_user_url(cloud_name, account_id)

    return data


def build_user_url(cloud_name: str | None, account_id: str) -> str | None:
    """Build a URL to a specific Confluence user profile."""
    base_url = build_base_confluence_url(cloud_name)
    if not base_url or not account_id:
        return None

    return f"{base_url}/wiki/people/{account_id}"


def build_base_confluence_url(cloud_name: str | None) -> str | None:
    """Build the base Confluence URL for the cloud instance."""
    if not cloud_name:
        return None

    # Remove .atlassian.net suffix if present and add it back
    clean_name = cloud_name.replace(".atlassian.net", "")
    return f"https://{clean_name}.atlassian.net"
