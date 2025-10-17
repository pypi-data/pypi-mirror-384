"""Routines that would normally be a @tool, but need to be shared across modules.

We group these routines here to avoid circular imports and the need for doing imports
inside functions, for instance.
"""

import json
from typing import Any

from arcade_tdk import ToolContext
from arcade_tdk.errors import RetryableToolError
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.sites.item.site_item_request_builder import SiteItemRequestBuilder
from msgraph_beta.generated.models.entity_type import EntityType
from msgraph_beta.generated.models.search_query import SearchQuery
from msgraph_beta.generated.models.search_request import SearchRequest
from msgraph_beta.generated.search.query.query_post_request_body import QueryPostRequestBody

from arcade_sharepoint.client import get_client
from arcade_sharepoint.exceptions import SiteNotFoundError
from arcade_sharepoint.serializers import serialize_drive_item, serialize_site
from arcade_sharepoint.utils import get_site_identifier, is_site_id


async def get_site_id(context: ToolContext, site: str) -> str:
    """Retrieve the ID of a specific SharePoint site by its ID, URL, or name."""
    if is_site_id(site):
        return site
    site_response = await get_site(context=context, site=site)
    site_id = site_response.get("site_id")
    if not isinstance(site_id, str) or not site_id:
        raise SiteNotFoundError(site)
    return str(site_id)  # Explicit string cast to satisfy mypy


async def get_site(
    context: ToolContext, site: str, include_lists: bool = False, include_drives: bool = False
) -> dict[str, Any]:
    """Retrieve information about a specific SharePoint site by its ID, URL, or name."""
    client = get_client(context.get_auth_token_or_empty())
    site = site.strip()
    site_identifier = get_site_identifier(site)

    if site_identifier:
        expand = []
        params = {}

        if include_lists:
            expand.append("lists")

        if include_drives:
            expand.append("drives")

        if expand:
            params["expand"] = expand

        request_configuration = RequestConfiguration(
            query_parameters=SiteItemRequestBuilder.SiteItemRequestBuilderGetQueryParameters(
                **params,
            ),
        )
        response = await client.sites.by_site_id(site_identifier).get(
            request_configuration=request_configuration
        )

        if not response:
            raise SiteNotFoundError(site_identifier)

        return serialize_site(response)

    else:
        search_response = await search_sites(context, keywords=site, limit=100)

        if search_response["count"] == 0:
            raise SiteNotFoundError(site)

        elif search_response["count"] > 1:
            message = f"Multiple sites found with identifier: '{site}'. Please specify a unique identifier."
            available_sites = [
                {
                    "site_id": site["site_id"],
                    "name": site["name"],
                    "display_name": site["display_name"],
                }
                for site in search_response["sites"]
            ]
            raise RetryableToolError(
                message=message,
                developer_message=message,
                additional_prompt_content=(
                    f"Available sites matching '{site}' are: {json.dumps(available_sites)}"
                ),
            )

        return await get_site(
            context,
            site=search_response["sites"][0]["site_id"],
            include_lists=include_lists,
            include_drives=include_drives,
        )


async def search_sites(
    context: ToolContext,
    keywords: str,
    limit: int = 10,
    offset: int = 0,
) -> dict[str, Any]:
    """Search for SharePoint sites by name or description.

    The Microsoft Graph API does not support pagination on this endpoint.
    """
    limit = min(100, max(1, limit))
    client = get_client(context.get_auth_token_or_empty())

    request_body = QueryPostRequestBody(
        requests=[
            SearchRequest(
                entity_types=[EntityType.Site],
                query=SearchQuery(query_string=keywords),
                from_=offset,
                size=limit,
            )
        ]
    )

    response = await client.search.query.post(request_body)

    if response and response.value and len(response.value) > 0:
        hits_container = (
            response.value[0].hits_containers[0] if response.value[0].hits_containers else None
        )
        search_hits = hits_container.hits if hits_container else []
        more_results = bool(hits_container.more_results_available) if hits_container else False
    else:
        search_hits = []
        more_results = False

    if not search_hits:
        return {"count": 0, "sites": []}

    sites = []
    for search_hit in search_hits:
        if search_hit.resource:
            try:
                # Cast the Entity to Site for type checking purposes
                # The search API returns Entity objects that are actually Site objects
                site_resource = search_hit.resource
                if hasattr(site_resource, "id") and hasattr(site_resource, "name"):
                    # Type ignore since we know this is actually a Site object from the search API
                    serialized_site = serialize_site(site_resource)  # type: ignore[arg-type]
                    sites.append(serialized_site)
            except (AttributeError, TypeError):
                # Skip invalid resources
                continue

    return {
        "sites": sites,
        "count": len(sites),
        "pagination": {
            "limit": limit,
            "current_offset": offset,
            "next_offset": offset + limit if more_results else None,
            "more_sites_available": more_results,
        },
    }


async def search_items_in_all_drives(
    context: ToolContext, keywords: str, limit: int, offset: int
) -> dict[str, Any]:
    """Search for items in all drives."""
    client = get_client(context.get_auth_token_or_empty())

    request_body = QueryPostRequestBody(
        requests=[
            SearchRequest(
                entity_types=[EntityType.DriveItem],
                query=SearchQuery(query_string=keywords),
                from_=offset,
                size=limit,
            )
        ]
    )

    response = await client.search.query.post(request_body)

    if response and response.value and len(response.value) > 0:
        hits_container = (
            response.value[0].hits_containers[0] if response.value[0].hits_containers else None
        )
        search_hits = hits_container.hits if hits_container else []
        more_results = bool(hits_container.more_results_available) if hits_container else False
    else:
        search_hits = []
        more_results = False

    if not search_hits:
        return {"count": 0, "items": []}

    items = []

    for search_hit in search_hits:
        item = search_hit.resource
        site_id = None
        drive_id = None
        if item and hasattr(item, "parent_reference") and item.parent_reference:
            if hasattr(item.parent_reference, "drive_id"):
                drive_id = item.parent_reference.drive_id
            if hasattr(item.parent_reference, "site_id"):
                site_id = item.parent_reference.site_id

        if item:  # Only serialize valid items
            try:
                # Type ignore since search API returns Entity objects that are actually DriveItem objects
                items.append(serialize_drive_item(item=item, site_id=site_id, drive_id=drive_id))  # type: ignore[arg-type]
            except (AttributeError, TypeError):
                # Skip invalid items
                continue

    return {
        "count": len(search_hits),
        "items": items,
        "pagination": {
            "limit": limit,
            "current_offset": offset,
            "next_offset": offset + limit if more_results else None,
            "more_items_available": more_results,
        },
    }
