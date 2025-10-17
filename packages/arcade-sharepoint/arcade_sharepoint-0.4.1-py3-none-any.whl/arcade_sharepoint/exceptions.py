from arcade_tdk.errors import ToolExecutionError


class SharePointToolExecutionError(ToolExecutionError):
    pass


class SiteNotFoundError(SharePointToolExecutionError):
    """Raised when a site is not found."""

    def __init__(self, site_identifier: str):
        self.site_identifier = site_identifier
        message = f"Site with identifier '{site_identifier}' was not found."
        super().__init__(message=message, developer_message=message)
