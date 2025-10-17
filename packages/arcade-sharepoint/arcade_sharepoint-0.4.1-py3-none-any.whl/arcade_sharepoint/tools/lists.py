from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Microsoft
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.sites.item.lists.item.items.items_request_builder import (
    ItemsRequestBuilder,
)

import arcade_sharepoint.common as common
from arcade_sharepoint.client import get_client
from arcade_sharepoint.serializers import serialize_list_item


@tool(requires_auth=Microsoft(scopes=["Sites.Read.All"]))
async def get_lists_from_site(
    context: ToolContext,
    site: Annotated[
        str,
        "Site ID, SharePoint URL, or site name to get lists from. "
        "Prefer using a site ID whenever available for optimal performance.",
    ],
) -> Annotated[dict[str, Any], "The SharePoint site lists."]:
    """Retrieve lists from a SharePoint site."""
    site_data = await common.get_site(context=context, site=site, include_lists=True)
    site_id = site_data.get("site_id", "")
    lists = site_data.get("lists", [])
    return {"site_id": site_id, "lists": lists, "count": len(lists)}


@tool(requires_auth=Microsoft(scopes=["Sites.Read.All"]))
async def get_items_from_list(
    context: ToolContext,
    site: Annotated[
        str,
        "Site ID, SharePoint URL, or site name to get lists from. "
        "Prefer using a site ID whenever available for optimal performance.",
    ],
    list_id: Annotated[str, "The ID of the list to get items from."],
) -> Annotated[dict[str, Any], "The SharePoint list items."]:
    """Retrieve items from a list in a SharePoint site.

    Note: The Microsoft Graph API does not offer endpoints to retrieve list item attachments.
    Because of that, the only information we can get is whether the item has attachments or not.
    """
    client = get_client(context.get_auth_token_or_empty())

    site_id = await common.get_site_id(context=context, site=site)

    request_configuration = RequestConfiguration(
        query_parameters=ItemsRequestBuilder.ItemsRequestBuilderGetQueryParameters(
            expand=["fields"],
        ),
    )

    response = (
        await client.sites.by_site_id(site_id)
        .lists.by_list_id(list_id)
        .items.get(request_configuration)
    )

    if not response or not response.value:
        return {"items": [], "count": 0}

    items = [serialize_list_item(item, site_id, list_id) for item in response.value if item]

    return {"items": items, "count": len(items)}
