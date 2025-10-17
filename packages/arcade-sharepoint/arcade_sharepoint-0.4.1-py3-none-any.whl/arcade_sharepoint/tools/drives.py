from typing import Annotated, Any

from arcade_tdk import ToolContext, tool
from arcade_tdk.auth import Microsoft
from arcade_tdk.errors import ToolExecutionError
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.drives.item.items.item.children.children_request_builder import (
    ChildrenRequestBuilder,
)

# SearchWithQRequestBuilder imports are now done locally to avoid type conflicts
from msgraph.generated.drives.item.root.root_request_builder import RootRequestBuilder

import arcade_sharepoint.common as common
from arcade_sharepoint.client import get_client
from arcade_sharepoint.serializers import serialize_drive_item


@tool(requires_auth=Microsoft(scopes=["Sites.Read.All"]))
async def get_drives_from_site(
    context: ToolContext,
    site: Annotated[
        str,
        "Site ID, SharePoint URL, or site name to get drives from. "
        "Prefer using a site ID whenever available for optimal performance.",
    ],
) -> Annotated[dict[str, Any], "The drives from the SharePoint site."]:
    """Retrieve drives / document libraries from a SharePoint site.

    If you have a site name, it is not necessary to call Sharepoint.SearchSites first. You can simply
    call this tool with the site name / keywords.
    """
    site_data = await common.get_site(context=context, site=site, include_drives=True)
    drives = site_data.get("drives", [])
    return {"drives": drives, "count": len(drives)}


@tool(requires_auth=Microsoft(scopes=["Sites.Read.All"]))
async def list_root_items_in_drive(
    context: ToolContext,
    drive_id: Annotated[str, "The ID of the drive to get items from."],
    limit: Annotated[int, "The number of items to get. Defaults to 100, max is 500."] = 100,
    offset: Annotated[int, "The number of items to skip."] = 0,
) -> Annotated[dict[str, Any], "The items from the root of a drive in a SharePoint site."]:
    """Retrieve items from the root of a drive in a SharePoint site.

    Note: Due to how the Microsoft Graph API is designed, we have to retrieve all items, including the ones
    skipped by offset. For this reason, the tool execution time tends to increase with the offset value.
    """
    limit = max(1, min(limit, 500))
    offset = max(0, offset)

    client = get_client(context.get_auth_token_or_empty())

    request_configuration = RequestConfiguration(
        query_parameters=RootRequestBuilder.RootRequestBuilderGetQueryParameters(
            expand=["children"],
        ),
    )

    response = await client.drives.by_drive_id(drive_id).root.get(request_configuration)

    if not response or not response.children:
        return {"items": [], "count": 0}

    items = [
        serialize_drive_item(item=item, drive_id=drive_id)
        for item in response.children[offset : offset + limit]
    ]

    return {
        "items": items,
        "count": len(items),
        "pagination": {
            "limit": limit,
            "current_offset": offset,
            "next_offset": offset + limit
            if response.children and len(response.children) > offset + limit
            else None,
            "more_items_available": response.children is not None
            and len(response.children) > offset + limit,
        },
    }


@tool(requires_auth=Microsoft(scopes=["Sites.Read.All"]))
async def list_items_in_folder(
    context: ToolContext,
    drive_id: Annotated[str, "The ID of the drive to get items from."],
    folder_id: Annotated[str, "The ID of the folder to get items from."],
    limit: Annotated[int, "The number of items to get. Defaults to 100, max is 500."] = 100,
    offset: Annotated[int, "The number of items to skip."] = 0,
) -> Annotated[dict[str, Any], "The items from the folder in the drive."]:
    """Retrieve items from a folder in a drive in a SharePoint site.

    Note: Due to how the Microsoft Graph API is designed, we have to retrieve all items, including the ones
    skipped by offset. For this reason, the tool execution time tends to increase with the offset value.
    """
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    client = get_client(context.get_auth_token_or_empty())

    request_configuration = RequestConfiguration(
        query_parameters=ChildrenRequestBuilder.ChildrenRequestBuilderGetQueryParameters(
            top=limit + offset,
        ),
    )

    response = (
        await client.drives.by_drive_id(drive_id)
        .items.by_drive_item_id(folder_id)
        .children.get(request_configuration)
    )

    if not response or not response.value:
        return {"items": [], "count": 0}

    item_objects = response.value[offset : offset + limit]

    items = [
        serialize_drive_item(item=item, drive_id=drive_id, parent_folder_id=folder_id)
        for item in item_objects
    ]

    return {
        "items": items,
        "count": len(items),
        "pagination": {
            "limit": limit,
            "current_offset": offset,
            "next_offset": offset + limit
            if response and response.odata_next_link is not None
            else None,
            "more_items_available": response is not None and response.odata_next_link is not None,
        },
    }


@tool(requires_auth=Microsoft(scopes=["Sites.Read.All"]))
async def search_drive_items(
    context: ToolContext,
    keywords: Annotated[str, "The keywords to search for files in the drive."],
    drive_id: Annotated[
        str | None,
        "Optionally, the ID of the drive to search items in. "
        "If not provided, the search will be performed in all drives.",
    ] = None,
    folder_id: Annotated[
        str | None,
        "Optionally narrow the search within a specific folder by its ID. "
        "If not provided, the search will be performed in the whole drive. "
        "If a folder_id is provided, it is required to provide a drive_id as well.",
    ] = None,
    limit: Annotated[int, "The number of files to get. Defaults to 50, max is 500."] = 50,
    offset: Annotated[int, "The number of files to skip."] = 0,
) -> Annotated[dict[str, Any], "The items from the drive(s)."]:
    """Search for items in one or more Sharepoint drives.

    Note: when searching within a single Drive and/or Folder, due to how the Microsoft Graph API is designed,
    we have to retrieve all items, including the ones skipped by offset. For this reason, the tool execution
    time tends to increase with the offset value.
    """
    limit = min(50, max(1, limit))
    offset = max(0, offset)

    if not drive_id:
        if folder_id:
            raise ToolExecutionError(
                "In order to filter by folder_id, it is required to provide a drive_id as well."
            )

        return await common.search_items_in_all_drives(
            context=context,
            keywords=keywords,
            limit=limit,
            offset=offset,
        )

    client = get_client(context.get_auth_token_or_empty())

    # Import response types for union typing
    from msgraph.generated.drives.item.items.item.search_with_q.search_with_q_get_response import (
        SearchWithQGetResponse as FolderSearchResponse,
    )
    from msgraph.generated.drives.item.search_with_q.search_with_q_get_response import (
        SearchWithQGetResponse as DriveSearchResponse,
    )

    response: DriveSearchResponse | FolderSearchResponse | None = None

    if folder_id:
        # Use the folder-specific search endpoint
        from msgraph.generated.drives.item.items.item.search_with_q.search_with_q_request_builder import (
            SearchWithQRequestBuilder as FolderSearchBuilder,
        )

        folder_request_configuration = RequestConfiguration(
            query_parameters=FolderSearchBuilder.SearchWithQRequestBuilderGetQueryParameters(
                top=limit + offset,
            ),
        )
        response = (
            await client.drives.by_drive_id(drive_id)
            .items.by_drive_item_id(folder_id)
            .search_with_q(keywords)
            .get(folder_request_configuration)
        )

    else:
        # Use the drive-level search endpoint
        from msgraph.generated.drives.item.search_with_q.search_with_q_request_builder import (
            SearchWithQRequestBuilder as DriveSearchBuilder,
        )

        drive_request_configuration = RequestConfiguration(
            query_parameters=DriveSearchBuilder.SearchWithQRequestBuilderGetQueryParameters(
                top=limit + offset,
            ),
        )
        response = (
            await client.drives.by_drive_id(drive_id)
            .search_with_q(keywords)
            .get(drive_request_configuration)
        )

    if not response or not response.value:
        return {"count": 0, "items": []}

    items = [
        serialize_drive_item(item=item, drive_id=drive_id, parent_folder_id=folder_id)
        for item in response.value[offset : offset + limit]
    ]

    return {
        "count": len(items),
        "items": items,
        "pagination": {
            "limit": limit,
            "current_offset": offset,
            "next_offset": offset + limit
            if response and response.odata_next_link is not None
            else None,
            "more_items_available": response is not None and response.odata_next_link is not None,
        },
    }
