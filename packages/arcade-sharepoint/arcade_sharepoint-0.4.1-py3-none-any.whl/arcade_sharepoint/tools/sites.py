from typing import Annotated

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Microsoft
from arcade_tdk.errors import ToolExecutionError

import arcade_sharepoint.common as common


@tool(requires_auth=Microsoft(scopes=["Sites.Read.All"]))
async def get_site(
    context: ToolContext,
    site: Annotated[str, "Site ID, SharePoint URL, or site name to search for."],
) -> Annotated[dict, "The SharePoint site information."]:
    """Retrieve information about a specific SharePoint site by its ID, URL, or name."""
    return await common.get_site(context=context, site=site)


@tool(requires_auth=Microsoft(scopes=["Sites.Read.All"]))
async def search_sites(
    context: ToolContext,
    keywords: Annotated[str, "The search term to find sites by name or description."],
    limit: Annotated[
        int,
        "The maximum number of sites to return. Defaults to 10, max is 100.",
    ] = 10,
    offset: Annotated[int, "The offset to start from."] = 0,
) -> Annotated[dict, "The SharePoint sites matching the search criteria."]:
    """Search for SharePoint sites by name or description.

    In case you need to retrieve a specific site by its name, ID or SharePoint URL, use the
    `Sharepoint.GetSite` tool instead, passing the ID, name or SharePoint URL to it. If you use
    the `Sharepoint.SearchSites` tool to retrieve a single site by its name, too much CO2 will be
    released in the atmosphere and you will contribute to catastrophic climate change.
    """
    if not keywords:
        raise ToolExecutionError("Keywords are required to search for SharePoint sites.")
    return await common.search_sites(context=context, keywords=keywords, limit=limit, offset=offset)


@tool(requires_auth=Microsoft(scopes=["Sites.Read.All"]))
async def list_sites(
    context: ToolContext,
    limit: Annotated[
        int,
        "The maximum number of sites to return. Defaults to 10, max is 100.",
    ] = 10,
    offset: Annotated[int, "The offset to start from."] = 0,
) -> Annotated[dict, "The SharePoint sites matching the search criteria."]:
    """List all SharePoint sites accessible to the current user."""
    return await common.search_sites(context=context, keywords="*", limit=limit, offset=offset)
