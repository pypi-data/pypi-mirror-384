"""File model definitions."""

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Author(BaseModel):
    """Author information model."""

    id: UUID
    name: str


class File(BaseModel):
    """File or directory model."""

    # New API fields (made optional for flexibility)
    name: str | None = None
    path: str | None = None
    type: str | None = None  # 'file' or 'folder'
    size: int = 0
    last_modified: datetime | None = Field(alias="lastModified", default=None)
    etag: str | None = None
    content_type: str | None = Field(alias="contentType", default=None)
    storage_class: str | None = Field(alias="storageClass", default=None)
    version_id: str | None = Field(alias="versionId", default=None)

    # Old API fields (for backward compatibility)
    object_name: str | None = Field(alias="objectName", default=None)
    is_dir: bool | None = Field(alias="isDir", default=None)
    is_directory: bool | None = Field(alias="isDirectory", default=None)  # Real API field
    url: str | None = None
    metadata: dict[str, Any] | None = None
    object_key: str | None = Field(alias="objectKey", default=None)
    logical_path: str | None = Field(alias="logicalPath", default=None)
    created_at: datetime | None = Field(alias="createdAt", default=None)
    author: Author | None = None
    last_modified_by: Author | None = Field(alias="lastModifiedBy", default=None)

    # For backward compatibility
    hash: str | None = None

    def get_is_directory(self) -> bool:
        """Check if this is a directory."""
        # Check is_directory field first (real API field)
        if self.is_directory is not None:
            return self.is_directory
        # Check is_dir field (old API)
        if self.is_dir is not None:
            return self.is_dir
        # Then check type field
        elif self.type:
            return self.type == "folder"
        # Finally check path patterns
        if self.object_name and self.object_name.endswith("/"):
            return True
        if self.logical_path and self.logical_path.endswith("/"):
            return True
        if self.path and self.path.endswith("/"):
            return True
        return False

    def __init__(self, **data):
        """Initialize File with name extraction from objectName if needed."""
        super().__init__(**data)
        # Auto-set name from objectName if name is not provided
        if not self.name and self.object_name:
            # Extract filename from path-like objectName
            import os

            self.name = os.path.basename(self.object_name.rstrip("/"))
            if not self.name:  # If basename is empty (root path), use the folder name
                parts = [p for p in self.object_name.rstrip("/").split("/") if p]
                self.name = parts[-1] if parts else self.object_name

        # Set type based on is_directory if type is not set
        if not self.type and self.is_directory is not None:
            self.type = "folder" if self.is_directory else "file"

        # Set is_directory based on type if is_directory is not set
        if self.is_directory is None and self.type is not None:
            self.is_directory = self.type == "folder"

    @property
    def actual_path(self) -> str:
        """Get the actual path for API operations."""
        # For manually created ".." entries, always use path field (not name)
        if self.name == "..":
            # Use path field for navigation entries (contains parent path or special markers)
            return self.path or ""

        # For regular files, prefer logicalPath over path for new API
        if self.logical_path:
            return self.logical_path
        elif self.path:
            return self.path
        elif self.object_name:
            return self.object_name
        else:
            return self.name or ""

    model_config = ConfigDict(populate_by_name=True)


class FileDownloadInfo(BaseModel):
    """File download information model."""

    path: str
    name: str
    size: int
    type: str
    presigned_url: str = Field(alias="presignedUrl")

    model_config = ConfigDict(populate_by_name=True)


class FailedDownload(BaseModel):
    """Failed download information model."""

    path: str
    name: str
    error: str

    model_config = ConfigDict(frozen=True)


class BatchDownloadResult(BaseModel):
    """Simple container for batch download results when raise_on_failure=False.

    For helper properties, use BatchDownloadError which provides:
    - success_count, failure_count, total_count
    - is_complete, has_failures, success_rate

    Example:
        >>> result = await client.download_batch(repo_id, paths, raise_on_failure=False)
        >>> print(f"Downloaded {len(result.successful)}/{len(result.successful) + len(result.failed)}")
        >>> for failure in result.failed:
        ...     retry(failure)
    """

    successful: list[Path]
    failed: list[FailedDownload]

    model_config = ConfigDict(frozen=True)
