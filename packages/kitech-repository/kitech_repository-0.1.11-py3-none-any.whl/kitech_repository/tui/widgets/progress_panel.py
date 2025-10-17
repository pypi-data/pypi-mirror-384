"""
Progress panel widget for displaying file operation progress.

This widget shows the current file operation status, progress bar, and operation details.
"""

from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import ProgressBar, Static

from kitech_repository.tui.models import FileOperation, OperationStatus


class ProgressPanel(Container):
    """
    Widget for displaying file transfer progress.

    Shows:
    - Progress bar with percentage
    - Operation description (download/upload)
    - Current file being transferred
    - Status (pending, in progress, completed, failed)
    """

    # Reactive properties that trigger UI updates
    current_operation: reactive[FileOperation | None] = reactive(None)
    is_visible: reactive[bool] = reactive(False)
    # Batch operation tracking (T067)
    current_file_number: reactive[int] = reactive(0)
    total_files: reactive[int] = reactive(0)
    # Timer tracking for auto-hide
    _auto_hide_timer = None

    def compose(self):
        """Compose the progress panel UI components."""
        yield Static("", id="operation-status", classes="status-info")
        yield ProgressBar(total=100, id="progress-bar")
        yield Static("", id="operation-details", classes="status-info")

    def watch_current_operation(self, old: FileOperation | None, new: FileOperation | None) -> None:
        """
        React to current operation changes.

        Updates the progress bar and status text when a new operation starts
        or when the current operation is updated.

        Args:
            old: Previous operation (if any)
            new: New current operation (if any)
        """
        if new is None:
            # No operation - hide panel
            self.is_visible = False
            self.add_class("hidden")
            return

        # Show panel and update content
        self.is_visible = True
        self.remove_class("hidden")
        self._update_progress_display(new)

    def watch_is_visible(self, old: bool, new: bool) -> None:
        """
        React to visibility changes.

        Args:
            old: Previous visibility state
            new: New visibility state
        """
        if new:
            self.remove_class("hidden")
        else:
            self.add_class("hidden")

    def _update_progress_display(self, operation: FileOperation) -> None:
        """
        Update the progress bar and status text.

        Includes batch file progress display (T067).

        Args:
            operation: The file operation to display
        """
        # Update progress bar
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.update(progress=operation.progress_percent)

        # Update status text based on operation status
        status_widget = self.query_one("#operation-status", Static)
        details_widget = self.query_one("#operation-details", Static)

        # Build batch progress prefix if tracking multiple files (T067)
        batch_prefix = ""
        if self.total_files > 1 and self.current_file_number > 0:
            batch_prefix = f"[{self.current_file_number}/{self.total_files}] "

        if operation.status == OperationStatus.PENDING:
            status_widget.update(f"⏳ {batch_prefix}{operation.operation_type.title()} pending...")
            status_widget.set_class(True, "status-info")
        elif operation.status == OperationStatus.PREPARING:
            status_widget.update(f"🔄 {batch_prefix}{operation.operation_type.title()} preparing files...")
            status_widget.set_class(True, "status-info")
        elif operation.status == OperationStatus.IN_PROGRESS:
            status_widget.update(f"⬇️ {batch_prefix}{operation.operation_type.title()} in progress...")
            status_widget.set_class(True, "status-info")
        elif operation.status == OperationStatus.COMPLETED:
            # Success confirmation message (T066)
            status_widget.update(f"✓ {batch_prefix}{operation.operation_type.title()} completed successfully")
            status_widget.set_class(True, "status-success")
        elif operation.status == OperationStatus.FAILED:
            status_widget.update(f"✗ {batch_prefix}{operation.operation_type.title()} failed")
            status_widget.set_class(True, "status-error")
        elif operation.status == OperationStatus.CANCELLED:
            status_widget.update(f"⊗ {batch_prefix}{operation.operation_type.title()} cancelled")
            status_widget.set_class(True, "status-warning")

        # Update operation details with file name and progress (T067)
        file_path = operation.file_path
        # Extract just the filename for cleaner display
        file_name = file_path.split("/")[-1] if "/" in file_path else file_path

        # Show "Preparing..." instead of percentage when in PREPARING state
        if operation.status == OperationStatus.PREPARING:
            progress_text = "Preparing..."
        else:
            progress_text = f"{operation.progress_percent:.1f}%"

        if operation.total_bytes:
            # Show bytes transferred if available
            mb_transferred = operation.bytes_transferred / (1024 * 1024)
            mb_total = operation.total_bytes / (1024 * 1024)
            size_text = f" ({mb_transferred:.1f} MB / {mb_total:.1f} MB)"
        else:
            size_text = ""

        # Include current file name in batch operations (T067)
        if batch_prefix:
            details_widget.update(f"File: {file_name} - {progress_text}{size_text}")
        else:
            details_widget.update(f"{file_name} - {progress_text}{size_text}")

        if operation.error_message:
            details_widget.update(f"{file_name} - Error: {operation.error_message}")
            details_widget.set_class(True, "status-error")
        else:
            details_widget.set_class(True, "status-info")

    def on_file_operation_started(self, message) -> None:
        """
        Handle FileOperationStarted messages.

        This is the CRITICAL handler that was missing - without it, current_operation
        stays None and all subsequent progress/completed messages are ignored!

        Args:
            message: FileOperationStarted message with operation details
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info("=== ProgressPanel.on_file_operation_started CALLED ===")
        logger.info(f"Operation ID: {message.operation.operation_id}")
        logger.info(f"Operation type: {message.operation.operation_type}")

        # Cancel any pending auto-hide timer from previous operation
        if self._auto_hide_timer is not None:
            logger.info("Cancelling pending auto-hide timer from previous operation")
            self._auto_hide_timer.stop()
            self._auto_hide_timer = None

        # Set the current operation - this triggers watch_current_operation
        # which shows the panel and updates the display
        logger.info("Setting current_operation (this triggers watch_current_operation)")
        self.current_operation = message.operation
        logger.info(f"current_operation set. is_visible: {self.is_visible}")

    def on_file_operation_progress(self, message) -> None:
        """
        Handle FileOperationProgress messages.

        Updates the progress bar when progress updates are received.

        Args:
            message: FileOperationProgress message with operation_id and progress_percent
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"=== ProgressPanel.on_file_operation_progress CALLED ===")
        logger.info(f"Message operation_id: {message.operation_id}, progress: {message.progress_percent}%")
        logger.info(f"current_operation: {self.current_operation.operation_id if self.current_operation else 'None'}")

        if self.current_operation and message.operation_id == self.current_operation.operation_id:
            logger.info("Operation ID matches, updating progress")
            # Update progress percentage
            self.current_operation.progress_percent = message.progress_percent
            self._update_progress_display(self.current_operation)
            logger.info(f"Progress updated to {message.progress_percent}%")
        else:
            logger.warning(f"Operation ID mismatch or no current_operation! Ignoring progress update.")

    def on_file_operation_completed(self, message) -> None:
        """
        Handle FileOperationCompleted messages.

        Shows completion status and auto-hides after 2-3 seconds for successful operations (T066).

        Args:
            message: FileOperationCompleted message with success status and optional error
        """
        if self.current_operation and message.operation_id == self.current_operation.operation_id:
            # Update operation status
            if message.success:
                self.current_operation.status = OperationStatus.COMPLETED
                self.current_operation.progress_percent = 100.0
            else:
                self.current_operation.status = OperationStatus.FAILED
                self.current_operation.error_message = message.error

            self._update_progress_display(self.current_operation)

            # Auto-hide after 2.5 seconds if successful (T066)
            # Store the timer so it can be cancelled if a new operation starts
            if message.success:
                self._auto_hide_timer = self.set_timer(2.5, self._auto_hide)
            else:
                # For errors, stay visible longer (5 seconds) so user can read the error
                self._auto_hide_timer = self.set_timer(5.0, self._auto_hide)

    def _auto_hide(self) -> None:
        """Auto-hide the progress panel after successful completion."""
        self.current_operation = None
        self.is_visible = False
        self._auto_hide_timer = None
