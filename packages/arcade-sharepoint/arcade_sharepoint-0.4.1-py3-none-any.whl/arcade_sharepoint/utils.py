import uuid
from typing import Any
from urllib.parse import urlparse


def remove_none_values(data: dict[str, Any]) -> dict[str, Any]:
    """Remove None values from a dictionary."""
    return {k: v for k, v in data.items() if v is not None}


def get_site_identifier(value: str) -> str | None:
    """Get the site identifier from a value.

    The site identifier could be the site ID or a relative path: `{hostname}:/{path-to-site}`.

    If the value is not a valid site identifier, the function will return None.
    """
    if is_site_id(value):
        return value

    elif is_site_url(value):
        hostname, relative_path = get_site_identifiers_from_url(value)

        return f"{hostname}:/{relative_path}"

    return None


def is_site_url(url: str) -> bool:
    """Check if URL is a valid SharePoint Site URL."""
    if "http" not in url.lower():
        url = f"https://{url}"

    parsed = urlparse(url)

    if "sharepoint.com" not in parsed.netloc.lower():
        return False

    if not parsed.path.startswith("/sites/"):
        return False

    return len(parsed.path.lower().replace("/sites/", "")) > 0


def get_site_identifiers_from_url(url: str) -> tuple[str, str]:
    """Get the site's hostname and relative path from a SharePoint Site URL."""
    if "http" not in url.lower():
        url = f"https://{url}"

    parsed = urlparse(url)
    return parsed.netloc, parsed.path.strip("/")


def is_site_id(value: str) -> bool:
    parts = value.split(",")

    if len(parts) != 3:
        return False

    if not is_guid(parts[1]) or not is_guid(parts[2]):
        return False

    return ".sharepoint.com" in parts[0].lower()


def is_guid(value: str) -> bool:
    """Check if value is a SharePoint site ID (GUID format)."""
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    else:
        return True


def human_friendly_bytes_size(size: int) -> str:
    """Convert a bytes size to a human friendly string."""
    if size < 1024:
        value, unit = f"{size}", "B"
    elif size < 1024 * 1024:
        value, unit = f"{size / 1024:.1f}", "KB"
    elif size < 1024 * 1024 * 1024:
        value, unit = f"{size / (1024 * 1024):.1f}", "MB"
    elif size < 1024 * 1024 * 1024 * 1024:
        value, unit = f"{size / (1024 * 1024 * 1024):.1f}", "GB"
    else:
        value, unit = f"{size / (1024 * 1024 * 1024 * 1024):.1f}", "TB"

    return f"{value.replace('.0', '')} {unit}"
