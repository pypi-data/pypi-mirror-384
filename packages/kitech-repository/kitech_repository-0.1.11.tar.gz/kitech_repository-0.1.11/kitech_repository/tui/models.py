"""
Data models for KITECH Repository Manager TUI.

These models define the structure of data used in the Textual TUI,
separate from the core API models to allow for UI-specific fields and state management.
"""

from enum import Enum

from pydantic import BaseModel, Field


class PanelType(str, Enum):
    """Type of file panel in the dual-panel interface."""

    LOCAL = "local"
    REMOTE = "remote"


class PanelState(BaseModel):
    """
    State of a file panel (local or remote).

    This model tracks the reactive state of a panel widget,
    including current path, focus state, and loading status.
    """

    panel_type: PanelType
    current_path: str = Field(description="Current directory path being displayed")
    repository_id: int | None = Field(default=None, description="Repository ID for remote panel")
    repository_name: str | None = Field(default=None, description="Repository name for display")
    has_focus: bool = Field(default=False, description="Whether this panel currently has focus")
    is_loading: bool = Field(default=False, description="Whether the panel is loading data")

    model_config = {"use_enum_values": True}


class OperationStatus(str, Enum):
    """Status of a file operation."""

    PENDING = "pending"
    PREPARING = "preparing"  # Preparing file list for batch operations
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileOperation(BaseModel):
    """
    Represents a single file transfer operation (download or upload).

    This model tracks the progress and status of individual file operations
    for display in the progress panel and status messages.
    """

    operation_id: str = Field(description="Unique identifier for tracking this operation")
    operation_type: str = Field(description="Type of operation: 'download' or 'upload'")
    file_path: str = Field(description="Path to the file being transferred")
    local_path: str | None = Field(default=None, description="Local filesystem path")
    remote_path: str | None = Field(default=None, description="Remote repository path")
    status: OperationStatus = Field(default=OperationStatus.PENDING)
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress as percentage (0-100)")
    bytes_transferred: int = Field(default=0, ge=0, description="Number of bytes transferred")
    total_bytes: int | None = Field(default=None, ge=0, description="Total file size in bytes")
    error_message: str | None = Field(default=None, description="Error message if operation failed")

    model_config = {"use_enum_values": True}


class BatchOperation(BaseModel):
    """
    Batch file operation containing multiple file transfers.

    This model tracks overall progress for operations that involve multiple files,
    such as downloading all files in a directory or uploading a folder.
    """

    batch_id: str = Field(description="Unique identifier for this batch operation")
    operation_type: str = Field(description="Type of batch operation (e.g., 'download_all', 'upload_all')")
    total_files: int = Field(ge=0, description="Total number of files in this batch")
    completed_files: int = Field(default=0, ge=0, description="Number of files completed successfully")
    failed_files: int = Field(default=0, ge=0, description="Number of files that failed")
    operations: list[FileOperation] = Field(default_factory=list, description="Individual file operations")
    overall_status: OperationStatus = Field(default=OperationStatus.PENDING)

    @property
    def progress_percent(self) -> float:
        """
        Calculate overall batch progress as percentage.

        Returns:
            Progress as percentage (0-100), or 0.0 if no files
        """
        if self.total_files == 0:
            return 0.0
        return (self.completed_files / self.total_files) * 100.0

    model_config = {"use_enum_values": True}
