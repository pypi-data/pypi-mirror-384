from typing import Any

from msgraph.generated.models.audio import Audio
from msgraph.generated.models.base_site_page import BaseSitePage
from msgraph.generated.models.drive import Drive
from msgraph.generated.models.drive_item import DriveItem
from msgraph.generated.models.identity_set import IdentitySet
from msgraph.generated.models.image import Image
from msgraph.generated.models.list_ import List_
from msgraph.generated.models.list_item import ListItem
from msgraph.generated.models.photo import Photo
from msgraph.generated.models.quota import Quota
from msgraph.generated.models.remote_item import RemoteItem
from msgraph.generated.models.site import Site
from msgraph.generated.models.site_page import SitePage
from msgraph.generated.models.video import Video

from arcade_sharepoint.utils import human_friendly_bytes_size, remove_none_values


def serialize_site(site: Site) -> dict[str, Any]:
    """Serialize a SharePoint site object."""
    site_dict: dict[str, Any] = {
        "object_type": "site",
        "site_id": site.id,
        "name": site.name,
        "display_name": site.display_name,
        "description": site.description,
        "web_url": site.web_url,
        "created_at": (
            None
            if not site.created_date_time
            else site.created_date_time.strftime("%Y-%m-%d %H:%M:%S")
        ),
    }

    if site.lists and site.id:
        site_dict["lists"] = [serialize_list(list_, site.id) for list_ in site.lists]
    else:
        site_dict["lists"] = []

    if site.drives and site.id:
        site_dict["drives"] = [serialize_drive(drive, site.id) for drive in site.drives]
    else:
        site_dict["drives"] = []

    return site_dict


def serialize_site_page(page: BaseSitePage | SitePage, site_id: str) -> dict[str, Any]:
    """Serialize a SharePoint site page object."""
    page_dict = {
        "object_type": "site_page",
        "page_id": page.id,
        "name": page.name,
        "title": page.title,
        "description": page.description,
        "web_url": page.web_url,
        "show_comments": getattr(page, "show_comments", None),
        "thumbnail_web_url": getattr(page, "thumbnail_web_url", None),
        "comment_count": getattr(page, "comment_count", None),
        "like_count": getattr(page, "like_count", None),
        "view_count": getattr(page, "view_count", None),
        "created_by": None,
        "created_at": (
            None
            if not page.created_date_time
            else page.created_date_time.strftime("%Y-%m-%d %H:%M:%S")
        ),
        "page_layout": None,
        "publishing_state": None,
        "parent_site_id": site_id,
    }

    if page.created_by:
        page_dict["created_by"] = serialize_user_identity_set(page.created_by)

    if page.page_layout:
        page_dict["page_layout"] = page.page_layout.value

    if page.publishing_state and page.publishing_state.level:
        page_dict["publishing_state"] = page.publishing_state.level

    return page_dict


def serialize_user_identity_set(identity_set: IdentitySet) -> dict[str, Any] | None:
    """Serialize a SharePoint identity set object."""
    if not identity_set.user:
        return None

    user_data = {}

    if identity_set.user.id:
        user_data["user_id"] = identity_set.user.id

    if identity_set.user.display_name:
        user_data["user_display_name"] = identity_set.user.display_name

    if isinstance(identity_set.user.additional_data, dict):
        user_data.update(identity_set.user.additional_data)

    return user_data


def serialize_list(list_: List_, site_id: str) -> dict[str, Any]:
    """Serialize a SharePoint list object."""
    data = {
        "object_type": "list",
        "list_id": list_.id,
        "name": list_.name,
        "display_name": list_.display_name,
        "description": list_.description,
        "web_url": list_.web_url,
        "parent_site_id": site_id,
        "created_at": (
            None
            if not list_.created_date_time
            else list_.created_date_time.strftime("%Y-%m-%d %H:%M:%S")
        ),
    }

    return data


def serialize_list_item(item: ListItem, site_id: str, list_id: str) -> dict[str, Any]:
    """Serialize a SharePoint list item object.

    Note 1: The `web_url` field is present in the ListItem object, but it does not point
    to the real UI URL. It points to an empty file that gets downloaded when you try to
    open it in a browser. For that reason, we do not include it in the serialized data.
    """
    data = {
        "object_type": "list_item",
        "list_item_id": item.id,
        "title": None,
        "created_by": None,
        "created_at": (
            None
            if not item.created_date_time
            else item.created_date_time.strftime("%Y-%m-%d %H:%M:%S")
        ),
        "parent": {
            "site_id": site_id,
            "list_id": list_id,
        },
    }

    if item.created_by:
        data["created_by"] = serialize_user_identity_set(item.created_by)

    if item.fields and isinstance(item.fields.additional_data, dict):
        data["title"] = item.fields.additional_data.get("Title")

        if isinstance(item.fields.additional_data.get("Attachments"), bool):
            data["has_attachments"] = item.fields.additional_data.get("Attachments")

    return data


def serialize_drive(drive: Drive, site_id: str) -> dict[str, Any]:
    """Serialize a SharePoint drive object."""
    data = {
        "object_type": "site_drive",
        "drive_id": drive.id,
        "name": drive.name,
        "description": drive.description,
        "drive_type": drive.drive_type,
        "web_url": drive.web_url,
        "parent_site_id": site_id,
        "created_by": None,
        "created_at": (
            None
            if not drive.created_date_time
            else drive.created_date_time.strftime("%Y-%m-%d %H:%M:%S")
        ),
        "drive_size": serialize_drive_quota(drive.quota) if drive.quota else None,
    }

    if drive.created_by:
        data["created_by"] = serialize_user_identity_set(drive.created_by)

    return data


def serialize_drive_quota(quota: Quota) -> dict[str, Any] | None:
    """Serialize a SharePoint drive quota object."""
    if not quota or not isinstance(quota.total, int) or not isinstance(quota.used, int):
        return None

    return {
        "total": {
            "bytes": quota.total,
            "formatted": human_friendly_bytes_size(quota.total),
        },
        "used": {
            "bytes": quota.used,
            "formatted": human_friendly_bytes_size(quota.used),
            "percentage_used": f"{round((quota.used / quota.total) * 100, 1)}%",
        },
    }


def serialize_drive_item(
    item: DriveItem,
    site_id: str | None = None,
    drive_id: str | None = None,
    parent_folder_id: str | None = None,
) -> dict[str, Any]:
    """Serialize a SharePoint drive item object."""
    data: dict[str, Any] = {
        "object_type": "drive_item",
        "name": item.name,
    }

    if site_id:
        data["parent_site_id"] = site_id

    if drive_id:
        data["parent_drive_id"] = drive_id

    if parent_folder_id:
        data["parent_folder_id"] = parent_folder_id

    if item.size:
        data["size"] = {
            "bytes": item.size,
            "formatted": human_friendly_bytes_size(item.size),
        }

    children_data = serialize_drive_item_children(item, site_id, drive_id)
    if isinstance(children_data, dict):
        data.update(children_data)

    malware_data = serialize_drive_item_malware(item)
    if isinstance(malware_data, dict):
        data.update(malware_data)

    if item.web_url:
        data["web_url"] = item.web_url

    type_data = serialize_drive_item_type(item)
    if isinstance(type_data, dict):
        data.update(type_data)

    creation_data = serialize_drive_item_creation_metadata(item)
    if isinstance(creation_data, dict):
        data.update(creation_data)

    return data


def serialize_drive_item_children(
    item: DriveItem,
    site_id: str | None = None,
    drive_id: str | None = None,
) -> dict[str, Any]:
    """Serialize a SharePoint drive item children object."""
    data: dict[str, Any] = {}

    if item.children:
        data["children"] = [
            serialize_drive_item(
                item=child,
                site_id=site_id,
                drive_id=drive_id,
                parent_folder_id=item.id,
            )
            for child in item.children
        ]

    return data


def serialize_drive_item_malware(item: DriveItem) -> dict[str, Any]:
    """Serialize a SharePoint drive item malware object."""
    data: dict[str, Any] = {}

    if item.malware and item.malware.description:
        malware_data = {
            "description": item.malware.description,
        }
        if isinstance(item.malware.additional_data, dict):
            malware_data.update(item.malware.additional_data)
        data["malware"] = malware_data

    return data


def serialize_drive_item_type(item: DriveItem) -> dict[str, Any]:
    """Serialize a SharePoint drive item type object."""
    data: dict[str, Any] = {}

    if not item.folder and not item.file:
        data["item_id"] = item.id

    if item.folder:
        data["folder_id"] = item.id
        data["item_type"] = "folder"

    if item.file:
        data["file_id"] = item.id
        data["item_type"] = "file"
        data["mime_type"] = item.file.mime_type

    if item.package:
        data["item_type"] = "package"
        data["package_type"] = item.package.type

    if item.remote_item:
        data["remote_item"] = serialize_remote_item(item.remote_item)

    if item.workbook:
        data["item_type"] = "microsoft_excel_workbook"

    media_data = serialize_drive_item_file_media_type(item)
    if isinstance(media_data, dict):
        data.update(media_data)

    return data


def serialize_drive_item_file_media_type(item: DriveItem) -> dict[str, Any]:
    data: dict[str, Any] = {}

    if item.audio:
        data["item_type"] = "audio_file"
        data["audio"] = serialize_audio_file(item.audio)

    if item.image:
        data["item_type"] = "image_file"
        data["image"] = serialize_image_file(item.image)

    if item.photo:
        data["item_type"] = "photo_file"
        data["photo"] = serialize_photo(item.photo)

    if item.video:
        data["item_type"] = "video_file"
        data["video"] = serialize_video_file(item.video)

    return data


def serialize_drive_item_creation_metadata(item: DriveItem) -> dict[str, Any]:
    data: dict[str, Any] = {}

    if item.created_by:
        created_by_data = serialize_user_identity_set(item.created_by)
        if created_by_data is not None:
            data["created_by"] = created_by_data

    if item.file_system_info and item.file_system_info.created_date_time:
        data["created_at"] = item.file_system_info.created_date_time.strftime("%Y-%m-%d %H:%M:%S")

    return data


def serialize_audio_file(audio: Audio) -> dict[str, Any]:
    """Serialize a SharePoint audio file object."""
    return remove_none_values({
        "album": audio.album,
        "album_artist": audio.album_artist,
        "artist": audio.artist,
        "bitrate": audio.bitrate,
        "composers": audio.composers,
        "copyright": audio.copyright,
        "disc": audio.disc,
        "duration": audio.duration,
        "genre": audio.genre,
        "has_drm": audio.has_drm,
        "is_variable_bitrate": audio.is_variable_bitrate,
        "title": audio.title,
        "track": audio.track,
        "year": audio.year,
    })


def serialize_image_file(image: Image) -> dict[str, Any]:
    """Serialize a SharePoint image file object."""
    return remove_none_values({
        "width": image.width,
        "height": image.height,
    })


def serialize_video_file(video: Video) -> dict[str, Any]:
    """Serialize a SharePoint video file object."""
    return remove_none_values({
        "audio_format": video.audio_format,
        "audio_bits_per_sample": video.audio_bits_per_sample,
        "audio_channels": video.audio_channels,
        "audio_samples_per_second": video.audio_samples_per_second,
        "bitrate": video.bitrate,
        "duration": video.duration,
        "frame_rate": video.frame_rate,
        "four_character_code": video.four_c_c,
        "width": video.width,
        "height": video.height,
    })


def serialize_photo(photo: Photo) -> dict[str, Any]:
    """Serialize a SharePoint photo object."""
    return remove_none_values({
        "camera_make": photo.camera_make,
        "camera_model": photo.camera_model,
        "exposure_denominator": photo.exposure_denominator,
        "exposure_numerator": photo.exposure_numerator,
        "f_number": photo.f_number,
        "focal_length": photo.focal_length,
        "iso": photo.iso,
        "orientation": photo.orientation,
        "taken_date_time": (
            None
            if not photo.taken_date_time
            else photo.taken_date_time.strftime("%Y-%m-%d %H:%M:%S")
        ),
    })


def serialize_remote_item(remote_item: RemoteItem) -> dict[str, Any]:
    """Serialize a SharePoint remote item object."""
    data = {
        "_info": "This item is shared from a drive other than the one being accessed",
        "name": remote_item.name,
        "web_url": remote_item.web_url,
    }

    if remote_item.file:
        data["item_type"] = "file"
        data["file_id_in_the_remote_drive"] = remote_item.id
        data["mime_type"] = remote_item.file.mime_type
        # Note: remote_item.file doesn't have size attribute like DriveItem does

    if remote_item.folder:
        data["item_type"] = "folder"
        data["folder_id"] = remote_item.id

    return remove_none_values(data)
