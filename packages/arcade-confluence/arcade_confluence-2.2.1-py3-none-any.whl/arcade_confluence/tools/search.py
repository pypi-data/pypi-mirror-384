from typing import Annotated

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Atlassian

from arcade_confluence.client import ConfluenceClientV1
from arcade_confluence.utils import resolve_cloud_id


@tool(
    requires_auth=Atlassian(
        scopes=[
            "search:confluence",
            "read:page:confluence",  # Required by resolve_cloud_id
        ],
    )
)
async def search_content(
    context: ToolContext,
    must_contain_all: Annotated[
        list[str] | None,
        "Words/phrases that content MUST contain (AND logic). Each item can be:\n"
        "- Single word: 'banana' - content must contain this word\n"
        "- Multi-word phrase: 'How to' - content must contain all these words (in any order)\n"
        "- All items in this list must be present for content to match\n"
        "- Example: ['banana', 'apple'] finds content containing BOTH 'banana' AND 'apple'",
    ] = None,
    can_contain_any: Annotated[
        list[str] | None,
        "Words/phrases where content can contain ANY of these (OR logic). Each item can be:\n"
        "- Single word: 'project' - content containing this word will match\n"
        "- Multi-word phrase: 'pen & paper' - content containing all these words will match\n"
        "- Content matching ANY item in this list will be included\n"
        "- Example: ['project', 'documentation'] finds content with 'project' OR 'documentation'",
    ] = None,
    enable_fuzzy: Annotated[
        bool,
        "Enable fuzzy matching to find similar terms (e.g. 'roam' will find 'foam'). "
        "Defaults to True",
    ] = True,
    limit: Annotated[int, "Maximum number of results to return (1-100). Defaults to 25"] = 25,
    atlassian_cloud_id: Annotated[
        str | None,
        "The ID of the Atlassian Cloud to use (defaults to None). If not provided and the user has "
        "a single cloud authorized, the tool will use that. Otherwise, an error will be raised.",
    ] = None,
) -> Annotated[dict, "Search results containing content items matching the criteria"]:
    """Search for content in Confluence.

    The search is performed across all content in the authenticated user's Confluence workspace.
    All search terms in Confluence are case insensitive.

    You can use the parameters in different ways:
    - must_contain_all: For AND logic - content must contain ALL of these
    - can_contain_any: For OR logic - content can contain ANY of these
    - Combine them: must_contain_all=['banana'] AND can_contain_any=['database', 'guide']
    """
    atlassian_cloud_id = await resolve_cloud_id(context, atlassian_cloud_id)

    client = ConfluenceClientV1(
        token=context.get_auth_token_or_empty(),
        cloud_id=atlassian_cloud_id,
    )
    cql = client.construct_cql(must_contain_all, can_contain_any, enable_fuzzy)
    response = await client.get("search", params={"cql": cql, "limit": max(1, min(limit, 100))})

    return client.transform_search_content_response(response)
