"""
Local panel widget for displaying local filesystem.

This widget shows the current directory's files in a flat DataTable structure,
allowing navigation, file selection, and upload operations.
"""

from pathlib import Path

from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import DataTable, Static


class LocalPanel(Container):
    """
    Panel for browsing local filesystem.

    Features:
    - DataTable widget for flat directory display (current directory only)
    - Reactive focus management with visual indicators
    - Current path tracking (明確な現在位置)
    - Enter key to navigate into folders
    - Backspace key to go to parent directory
    - Upload operations (F3: upload all, F4: upload selected)
    """

    # Allow this container to receive keyboard focus
    can_focus = True

    # Reactive properties
    has_focus: reactive[bool] = reactive(False)
    current_path: reactive[Path] = reactive(Path.cwd())
    is_loading: reactive[bool] = reactive(False)

    DEFAULT_CSS = """
    LocalPanel {
        border: solid $primary;
        height: 1fr;
        width: 1fr;
    }

    LocalPanel.focused {
        border: solid yellow;
    }

    LocalPanel Static {
        background: $boost;
        color: $text;
        padding: 0 1;
    }

    LocalPanel DataTable {
        background: $surface;
        height: 1fr;
    }

    LocalPanel #error-message {
        color: red;
        margin: 1 2;
        text-align: center;
    }
    """

    BINDINGS = [
        ("f3", "upload_all", "Upload All"),
        ("f4", "upload_selected", "Upload Selected"),
        ("f5", "refresh", "Refresh"),
        ("backspace", "go_parent", "Parent Dir"),
    ]

    def __init__(self, **kwargs):
        """
        Initialize the local panel.

        Args:
            **kwargs: Additional arguments passed to Container
        """
        super().__init__(**kwargs)
        self._files: list[Path] = []

    def _is_operation_in_progress(self) -> bool:
        """
        Check if there's a file operation currently in progress.

        Checks the FileManagerScreen's global flag to prevent any operation
        (upload or download) from starting while another is active.

        Returns:
            True if any operation is active
        """
        try:
            from kitech_repository.tui.screens.file_manager import FileManagerScreen

            # Check global flag on FileManagerScreen
            if isinstance(self.screen, FileManagerScreen):
                return self.screen.is_operation_active
            return False
        except Exception:
            return False

    def compose(self):
        """Compose the local panel UI."""
        yield Static(f"Local: {self.current_path}", id="local-header", classes="panel-header")
        # Use DataTable to display files (flat structure)
        table = DataTable(id="local-table", cursor_type="row")
        table.add_columns("Type", "Name", "Size")
        yield table

    def on_mount(self) -> None:
        """Initialize panel when mounted."""
        self._update_header()
        self.load_files()

    def watch_has_focus(self, old: bool, new: bool) -> None:
        """
        React to focus changes.

        Updates the CSS class to show/hide visual focus indicator.

        Args:
            old: Previous focus state
            new: New focus state
        """
        if new:
            self.add_class("focused")
        else:
            self.remove_class("focused")

    def watch_current_path(self, old: Path, new: Path) -> None:
        """
        React to current path changes.

        Reloads the directory listing when path changes.

        Args:
            old: Previous path
            new: New path
        """
        if old != new:
            self._update_header()
            if self.is_mounted:
                self.load_files()

    def _update_header(self) -> None:
        """Update the header with current path."""
        try:
            header = self.query_one("#local-header", Static)
            header.update(f"Local: {self.current_path}")
        except Exception:
            # Header might not be mounted yet
            pass

    def load_files(self) -> None:
        """
        Load file list from current directory.

        Lists only the files and folders in the current directory (flat, non-recursive).
        Handles permission errors with actionable messages.
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            # List files in current directory
            self._files = sorted(
                self.current_path.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower())  # Directories first, then alphabetical
            )

            # Populate DataTable
            table = self.query_one("#local-table", DataTable)
            table.clear()

            for file_path in self._files:
                # Determine file type icon
                if file_path.is_dir():
                    file_type = "📁"
                    size_str = "-"
                elif file_path.is_file():
                    file_type = "📄"
                    # Get file size
                    try:
                        size_bytes = file_path.stat().st_size
                        if size_bytes < 1024:
                            size_str = f"{size_bytes} B"
                        elif size_bytes < 1024 * 1024:
                            size_str = f"{size_bytes / 1024:.1f} KB"
                        else:
                            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                    except Exception:
                        size_str = "?"
                else:
                    file_type = "❓"
                    size_str = "?"

                # Add row to table
                table.add_row(file_type, file_path.name, size_str)

            # Success - clear any error messages
            try:
                error_widget = self.query_one("#error-message", Static)
                error_widget.remove()
            except Exception:
                pass  # No error message to remove

        except PermissionError:
            # Permission denied - show actionable message
            logger.error(f"Permission denied: {self.current_path}")
            self._show_error(
                f"Permission Denied\n\n"
                f"You don't have permission to access: {self.current_path}\n\n"
                f"Action: Press Backspace to go to parent directory."
            )

        except OSError as e:
            # File system error - show actionable message
            logger.error(f"File system error: {e}")
            self._show_error(
                f"File System Error\n\n"
                f"Cannot access: {self.current_path}\n"
                f"Error: {str(e)}\n\n"
                f"Action: Press Backspace to go to parent directory."
            )

        except Exception as e:
            logger.error(f"Unexpected error loading files: {e}")
            self._show_error(f"Error: {str(e)}\n\nAction: Press F5 to retry.")

    def _show_error(self, message: str) -> None:
        """Show error message."""
        try:
            error_widget = self.query_one("#error-message", Static)
            error_widget.update(message)
        except Exception:
            # Error widget doesn't exist, create it
            self.mount(Static(message, id="error-message"))

    async def action_refresh(self) -> None:
        """
        Handle refresh action (F5 key).

        Reloads the current directory listing.
        """
        self.load_files()

    def on_file_operation_completed(self, message) -> None:
        """
        Handle file operation completed message.

        Auto-refresh the file list when an upload completes.

        Args:
            message: FileOperationCompleted message
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"LocalPanel: File operation completed, refreshing file list")

        # Auto-refresh after any file operation completes
        self.load_files()

    async def action_go_parent(self) -> None:
        """
        Handle go parent action (Backspace key).

        Navigates to the parent directory.
        """
        if self.current_path.parent != self.current_path:
            self.current_path = self.current_path.parent

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """
        Handle DataTable row selection (Enter key or click).

        If a folder is selected, navigate into it.

        Args:
            event: RowSelected event from DataTable
        """
        import logging
        logger = logging.getLogger(__name__)

        # Get the row index
        row_index = event.cursor_row

        if row_index is None or row_index < 0:
            return  # No file selected

        # Get file from internal list
        if row_index >= len(self._files):
            logger.warning(f"Invalid row index: {row_index}, files count: {len(self._files)}")
            return  # Invalid selection

        selected_path = self._files[row_index]
        logger.info(f"Row selected: {selected_path}, is_dir: {selected_path.is_dir()}")

        # Only navigate into directories
        if selected_path.is_dir():
            self.current_path = selected_path

    async def action_upload_selected(self) -> None:
        """
        Handle upload selected file or folder action (F4 key).

        Posts FileOperationStarted message for the selected file or folder.
        If a folder is selected, it uploads the entire folder with its structure.
        """
        import uuid

        # Check if another operation is already in progress
        if self._is_operation_in_progress():
            return

        from kitech_repository.tui.messages import FileOperationStarted
        from kitech_repository.tui.models import FileOperation, OperationStatus

        # Get selected file from table
        table = self.query_one("#local-table", DataTable)
        if table.cursor_row is None or table.cursor_row < 0:
            return  # No file selected

        # Get file from internal list
        if table.cursor_row >= len(self._files):
            return  # Invalid selection

        selected_path = self._files[table.cursor_row]

        # Determine operation type based on whether it's a file or directory
        if selected_path.is_dir():
            operation_type = "upload_all"  # Use upload_all for folders
        elif selected_path.is_file():
            operation_type = "upload"
        else:
            return  # Skip if neither file nor directory

        # Create file operation
        operation = FileOperation(
            operation_id=str(uuid.uuid4()),
            operation_type=operation_type,
            file_path=str(selected_path),
            local_path=str(selected_path),
            remote_path="",  # Upload to root by default
            status=OperationStatus.PENDING,
            progress_percent=0.0,
        )

        # Post message to start operation
        self.post_message(FileOperationStarted(operation=operation))

    def action_upload_all(self) -> None:
        """
        Handle upload all files action (F3 key).

        Shows confirmation dialog before starting batch upload of all files in current directory.
        """
        # Run in worker context to allow push_screen_wait
        self.run_worker(self._upload_all_worker())

    async def _upload_all_worker(self) -> None:
        """Worker for upload all operation."""
        import uuid

        # Check if another operation is already in progress
        if self._is_operation_in_progress():
            return

        from kitech_repository.tui.messages import FileOperationStarted
        from kitech_repository.tui.models import FileOperation, OperationStatus
        from kitech_repository.tui.widgets.confirmation_dialog import ConfirmationDialog

        # Show confirmation dialog
        confirmed = await self.app.push_screen_wait(
            ConfirmationDialog(
                f"Upload all files from '{self.current_path}'?\n\nThis will upload all files to the remote repository."
            )
        )

        if not confirmed:
            return  # User cancelled

        # Upload all files in current directory (non-recursive)
        # Create a batch operation for the current directory
        # Use "upload_current_dir" to distinguish from F4 (upload selected folder)
        operation = FileOperation(
            operation_id=str(uuid.uuid4()),
            operation_type="upload_current_dir",
            file_path=str(self.current_path),
            local_path=str(self.current_path),
            remote_path="",  # Upload to root by default
            status=OperationStatus.PENDING,
            progress_percent=0.0,
        )

        # Post message to start operation
        self.post_message(FileOperationStarted(operation=operation))
