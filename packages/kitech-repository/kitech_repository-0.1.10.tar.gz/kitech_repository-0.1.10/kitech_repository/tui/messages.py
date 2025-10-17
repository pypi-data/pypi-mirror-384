"""
Custom Textual messages for KITECH Repository Manager TUI.

Messages enable communication between widgets and app components.
Each message represents a specific event or action in the application.
"""

from textual.message import Message

from kitech_repository.tui.models import FileOperation, PanelType


class RepositorySelected(Message):
    """Posted when user selects a repository from the selection screen."""

    def __init__(self, repository_id: int, repository_name: str) -> None:
        """
        Initialize the message.

        Args:
            repository_id: ID of the selected repository
            repository_name: Name of the selected repository for display
        """
        self.repository_id = repository_id
        self.repository_name = repository_name
        super().__init__()


class FileOperationStarted(Message):
    """Posted when a file operation (download/upload) begins."""

    def __init__(self, operation: FileOperation) -> None:
        """
        Initialize the message.

        Args:
            operation: The file operation that started
        """
        self.operation = operation
        super().__init__()


class FileOperationProgress(Message):
    """Posted when file operation progress updates."""

    def __init__(self, operation_id: str, progress_percent: float) -> None:
        """
        Initialize the message.

        Args:
            operation_id: Unique ID of the operation
            progress_percent: Progress as percentage (0-100)
        """
        self.operation_id = operation_id
        self.progress_percent = progress_percent
        super().__init__()


class FileOperationCompleted(Message):
    """Posted when a file operation completes (success or failure)."""

    def __init__(self, operation_id: str, success: bool, error: str | None = None) -> None:
        """
        Initialize the message.

        Args:
            operation_id: Unique ID of the operation
            success: Whether the operation succeeded
            error: Error message if operation failed
        """
        self.operation_id = operation_id
        self.success = success
        self.error = error
        super().__init__()


class PanelFocusChanged(Message):
    """Posted when panel focus changes (Tab key navigation)."""

    def __init__(self, panel_type: PanelType) -> None:
        """
        Initialize the message.

        Args:
            panel_type: The type of panel that now has focus
        """
        self.panel_type = panel_type
        super().__init__()
