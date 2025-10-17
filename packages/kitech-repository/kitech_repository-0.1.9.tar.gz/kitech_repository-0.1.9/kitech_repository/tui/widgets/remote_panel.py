"""
Remote panel widget for displaying remote repository files.

This widget shows a directory tree of files in a remote repository and allows
navigation, file selection, and download operations.
"""

from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import DataTable, Static

from kitech_repository.core.client import KitechClient
from kitech_repository.core.exceptions import ApiError, AuthenticationError


class RemotePanel(Container):
    """
    Panel for browsing remote repository files.

    Features:
    - DataTable widget for remote file display
    - Reactive focus management with visual indicators
    - API integration for file list loading
    - Download operations (F1: download all, F2: download selected)
    """

    # Reactive properties
    has_focus: reactive[bool] = reactive(False)
    is_loading: reactive[bool] = reactive(False)
    current_path: reactive[str] = reactive("")

    DEFAULT_CSS = """
    RemotePanel {
        border: solid $primary;
        height: 1fr;
        width: 1fr;
    }

    RemotePanel.focused {
        border: solid yellow;
    }

    RemotePanel Static {
        background: $boost;
        color: $text;
        padding: 0 1;
    }

    RemotePanel DataTable {
        background: $surface;
        height: 1fr;
    }

    RemotePanel #loading-indicator {
        color: yellow;
        margin: 1 2;
    }

    RemotePanel #error-message {
        color: red;
        margin: 1 2;
        text-align: center;
    }

    RemotePanel LoadingIndicator {
        margin: 1 2;
    }
    """

    BINDINGS = [
        ("f1", "download_all", "Download All"),
        ("f2", "download_selected", "Download Selected"),
        ("f5", "refresh", "Refresh"),
        ("backspace", "go_parent", "Parent Dir"),
    ]

    def __init__(self, client: KitechClient, repository_id: int, repository_name: str, **kwargs):
        """
        Initialize the remote panel.

        Args:
            client: KitechClient instance for API calls
            repository_id: ID of the repository to browse
            repository_name: Name of the repository
            **kwargs: Additional arguments passed to Container
        """
        super().__init__(**kwargs)
        self.client = client
        self.repository_id = repository_id
        self.repository_name = repository_name
        self._files = []

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
        """Compose the remote panel UI."""
        yield Static(f"Remote: {self.repository_name}", id="remote-header", classes="panel-header")
        # Use DataTable to display remote files from API
        table = DataTable(id="remote-table", cursor_type="row")
        table.add_columns("Type", "Name", "Size")
        yield table

    async def on_mount(self) -> None:
        """Load files when panel is mounted."""
        await self.load_files()

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

    def watch_is_loading(self, old: bool, new: bool) -> None:
        """
        React to loading state changes.

        Shows/hides loading indicator when is_loading changes (T063).

        Args:
            old: Previous loading state
            new: New loading state
        """
        if not self.is_mounted:
            return

        # Update header to show loading status
        try:
            header = self.query_one("#remote-header", Static)
            if new:
                header.update(f"Remote: {self.repository_name} (Loading...)")
            else:
                header.update(f"Remote: {self.repository_name}")
        except Exception:
            # Header might not be mounted yet
            pass

    def watch_current_path(self, old: str, new: str) -> None:
        """
        React to current path changes.

        Reloads the file list when path changes.

        Args:
            old: Previous path
            new: New path
        """
        # Only reload if mounted and path actually changed
        if self.is_mounted and old != new:
            # Trigger file list reload when path changes
            # This will be fully implemented in Phase 8
            self.set_timer(0.1, self.load_files)

    async def load_files(self) -> None:
        """
        Load file list from API.

        Fetches files for the current path in the repository and updates the internal
        file list. This method runs the synchronous API call in a thread pool to avoid
        blocking the UI. Includes loading indicators and error handling (T063).
        """
        import asyncio
        import logging

        logger = logging.getLogger(__name__)

        # Set loading state (triggers watch_is_loading)
        self.is_loading = True

        try:
            # Call API to get file list (synchronous call, run in thread pool)
            result = await asyncio.to_thread(
                self.client.list_files, repository_id=self.repository_id, prefix=self.current_path
            )
            files = result.get("files", [])
            self._files = files

            # Populate DataTable with file list
            table = self.query_one("#remote-table", DataTable)
            table.clear()  # Clear existing rows

            for file in files:
                # Determine file type icon
                is_dir = file.get_is_directory()
                file_type = "📁" if is_dir else "📄"

                # Format file size
                if is_dir:
                    size_str = "-"
                elif file.size is not None:
                    # Convert bytes to human-readable format
                    if file.size < 1024:
                        size_str = f"{file.size} B"
                    elif file.size < 1024 * 1024:
                        size_str = f"{file.size / 1024:.1f} KB"
                    else:
                        size_str = f"{file.size / (1024 * 1024):.1f} MB"
                else:
                    size_str = "?"

                # Add row to table
                table.add_row(file_type, file.name, size_str)

            # Success - clear any error messages
            try:
                error_widget = self.query_one("#error-message", Static)
                await error_widget.remove()
            except Exception:
                pass  # No error message to remove

        except AuthenticationError as e:
            # Authentication error - show actionable message
            logger.error(f"Authentication error loading files: {e}")
            try:
                error_widget = self.query_one("#error-message", Static)
                error_widget.update(
                    f"Authentication Failed: {str(e)}\nAction: Run 'kitech-dev login' to re-authenticate."
                )
            except Exception:
                # Error widget doesn't exist, create it
                await self.mount(
                    Static(
                        f"Authentication Failed: {str(e)}\nAction: Run 'kitech-dev login' to re-authenticate.",
                        id="error-message",
                    )
                )

        except ApiError as e:
            # Network/API error - show actionable message
            logger.error(f"API error loading files: {e}")
            try:
                error_widget = self.query_one("#error-message", Static)
                error_widget.update(f"Network Error: {str(e)}\nAction: Check connection and press F5 to retry.")
            except Exception:
                # Error widget doesn't exist, create it
                await self.mount(
                    Static(
                        f"Network Error: {str(e)}\nAction: Check connection and press F5 to retry.", id="error-message"
                    )
                )

        except Exception as e:
            # Generic error - show actionable message
            logger.error(f"Unexpected error loading files: {e}")
            try:
                error_widget = self.query_one("#error-message", Static)
                error_widget.update(f"Error: {str(e)}\nAction: Press F5 to retry.")
            except Exception:
                # Error widget doesn't exist, create it
                await self.mount(Static(f"Error: {str(e)}\nAction: Press F5 to retry.", id="error-message"))

        finally:
            # Clear loading state
            self.is_loading = False

    async def action_refresh(self) -> None:
        """
        Handle refresh action (F5 key).

        Reloads the file list from the API.
        """
        await self.load_files()

    def on_file_operation_completed(self, message) -> None:
        """
        Handle file operation completed message.

        Auto-refresh the file list when an upload or download completes.

        Args:
            message: FileOperationCompleted message
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"RemotePanel: File operation completed, refreshing file list")

        # Auto-refresh after any file operation completes
        # Use set_timer to schedule the async load_files call
        self.set_timer(0.1, self.load_files)

    async def action_go_parent(self) -> None:
        """
        Handle go parent action (Backspace key).

        Navigates to the parent directory in the repository.
        """
        if self.current_path:
            # Remove last path component
            parts = self.current_path.rstrip("/").rsplit("/", 1)
            self.current_path = parts[0] if len(parts) > 1 else ""

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """
        Handle DataTable row selection (Enter key or click).

        If a folder is selected, navigate into it.
        If a file is selected, trigger download.

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

        selected_file = self._files[row_index]
        logger.info(f"Row selected: {selected_file.name}, is_dir: {selected_file.get_is_directory()}")

        # If it's a directory, navigate into it
        if selected_file.get_is_directory():
            # Update current_path to navigate into the folder
            if self.current_path:
                self.current_path = f"{self.current_path}/{selected_file.name}"
            else:
                self.current_path = selected_file.name
            logger.info(f"Navigating into directory: {self.current_path}")
        else:
            # If it's a file, trigger download action
            logger.info(f"File selected, triggering download: {selected_file.name}")
            self.run_action("download_selected")

    async def action_download_selected(self) -> None:
        """
        Handle download selected file action (F2 key).

        Posts FileOperationStarted message for the selected file.
        """
        import uuid
        import logging

        logger = logging.getLogger(__name__)
        logger.info("=== F2 DOWNLOAD SELECTED PRESSED ===")

        # Check if another operation is already in progress
        if self._is_operation_in_progress():
            logger.info("Operation already in progress, ignoring download request")
            return

        from kitech_repository.tui.messages import FileOperationStarted
        from kitech_repository.tui.models import FileOperation, OperationStatus

        # Get selected file from table
        table = self.query_one("#remote-table", DataTable)
        logger.info(f"Table cursor_row: {table.cursor_row}")

        if table.cursor_row is None or table.cursor_row < 0:
            logger.warning("No file selected (cursor_row is None or < 0)")
            return  # No file selected

        # Get file from internal list
        logger.info(f"Total files in _files: {len(self._files)}")
        if table.cursor_row >= len(self._files):
            logger.warning(f"Invalid selection: cursor_row {table.cursor_row} >= {len(self._files)}")
            return  # Invalid selection

        selected_file = self._files[table.cursor_row]
        selected_path = selected_file.path
        logger.info(f"Selected file: {selected_path}")

        # Create file operation
        operation = FileOperation(
            operation_id=str(uuid.uuid4()),
            operation_type="download",
            file_path=selected_path,
            remote_path=selected_path,
            local_path=None,  # Will be determined by handler
            status=OperationStatus.PENDING,
            progress_percent=0.0,
        )
        logger.info(f"Created operation: {operation.operation_id}, type: {operation.operation_type}")

        # Post message to start operation
        logger.info(f"Posting FileOperationStarted message for operation {operation.operation_id}")
        self.post_message(FileOperationStarted(operation=operation))
        logger.info("FileOperationStarted message posted successfully")

    def action_download_all(self) -> None:
        """
        Handle download all files action (F1 key).

        Shows confirmation dialog before starting batch download of current directory.
        """
        # Run in worker context to allow push_screen_wait
        self.run_worker(self._download_all_worker())

    async def _download_all_worker(self) -> None:
        """Worker for download all operation."""
        import uuid

        # Check if another operation is already in progress
        if self._is_operation_in_progress():
            return

        from kitech_repository.tui.messages import FileOperationStarted
        from kitech_repository.tui.models import FileOperation, OperationStatus
        from kitech_repository.tui.widgets.confirmation_dialog import ConfirmationDialog

        # Show confirmation dialog (T059)
        download_path = self.current_path if self.current_path else "root directory"
        confirmed = await self.app.push_screen_wait(
            ConfirmationDialog(
                f"Download all files from '{download_path}'?\n\nThis will download all files to ~/Downloads."
            )
        )

        if not confirmed:
            return  # User cancelled

        # Download entire current path (folder or root)
        download_path = self.current_path if self.current_path else None

        # Create file operation for batch download
        operation = FileOperation(
            operation_id=str(uuid.uuid4()),
            operation_type="download_all",
            file_path=download_path or "/",  # Root if no path
            remote_path=download_path,
            local_path=None,  # Will be determined by handler
            status=OperationStatus.PENDING,
            progress_percent=0.0,
        )

        # Post message to start operation
        self.post_message(FileOperationStarted(operation=operation))
