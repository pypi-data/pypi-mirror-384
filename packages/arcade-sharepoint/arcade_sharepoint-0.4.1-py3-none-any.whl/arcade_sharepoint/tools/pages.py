from typing import Annotated

import httpx
from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Microsoft
from arcade_tdk.errors import ToolExecutionError
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.sites.item.pages.graph_site_page.graph_site_page_request_builder import (
    GraphSitePageRequestBuilder,
)

import arcade_sharepoint.common as common
from arcade_sharepoint.client import get_client
from arcade_sharepoint.serializers import serialize_site_page


@tool(requires_auth=Microsoft(scopes=["Sites.Read.All"]))
async def get_page(
    context: ToolContext,
    site: Annotated[
        str,
        "Site ID, SharePoint URL, or site name to retrieve base pages from. "
        "Prefer using a site ID whenever available for optimal performance",
    ],
    page_id: Annotated[str, "The ID of the page to retrieve."],
    include_page_content: Annotated[
        bool,
        "Whether to include the page content in the response. Defaults to True. If set to False, "
        "the tool will return only the page metadata.",
    ] = True,
) -> Annotated[dict, "The page from the SharePoint site."]:
    """Retrieve metadata and the contents of a page in a SharePoint site.

    Page content is a list of Microsoft Sharepoint web part objects, such as text, images, banners,
    buttons, etc.

    If `include_page_content` is set to False, the tool will return only the page metadata.
    """
    client = get_client(context.get_auth_token_or_empty())

    site_id = await common.get_site_id(context=context, site=site)

    page_not_found = ToolExecutionError(f"Page with ID '{page_id}' not found in the Site '{site}'.")

    response = await client.sites.by_site_id(site_id).pages.by_base_site_page_id(page_id).get()

    if not response:
        raise page_not_found

    page = serialize_site_page(response, site_id=site_id)

    if include_page_content:
        async with httpx.AsyncClient() as http_client:
            content_response = await http_client.get(
                f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages/{page_id}/microsoft.graph.sitePage/webparts",
                params={"top": 200},
                headers={
                    "Authorization": f"Bearer {context.get_auth_token_or_empty()}",
                },
            )
            content_response.raise_for_status()

        content = content_response.json()
        page["content"] = content.get("value")

    return page


@tool(requires_auth=Microsoft(scopes=["Sites.Read.All"]))
async def list_pages(
    context: ToolContext,
    site: Annotated[
        str,
        "Site ID, SharePoint URL, or site name to retrieve base pages from. "
        "Prefer using a site ID whenever available for optimal performance.",
    ],
    limit: Annotated[
        int,
        "The maximum number of pages to return. Defaults to 10, max is 200.",
    ] = 10,
) -> Annotated[dict, "The pages from the SharePoint site."]:
    """Retrieve pages from a SharePoint site.

    The Microsoft Graph API does not support pagination on this endpoint.
    """
    # NOTE: although the Microsoft documentation says this endpoint supports pagination, it does not.
    # If you try to provide a skip or skiptoken parameter, you will get an error, despite responses
    # returning a `odata_next_link` property. ¯\_(ツ)_/¯
    limit = max(1, min(limit, 200))

    client = get_client(context.get_auth_token_or_empty())

    request_configuration = RequestConfiguration(
        query_parameters=GraphSitePageRequestBuilder.GraphSitePageRequestBuilderGetQueryParameters(
            top=limit,
        ),
    )

    site_id = await common.get_site_id(context=context, site=site)

    response = await client.sites.by_site_id(site_id).pages.graph_site_page.get(
        request_configuration
    )

    if not response or not response.value:
        return {"pages": [], "count": 0}

    return {
        "pages": [serialize_site_page(page, site_id) for page in response.value if page],
        "count": len([page for page in response.value if page]),
    }
