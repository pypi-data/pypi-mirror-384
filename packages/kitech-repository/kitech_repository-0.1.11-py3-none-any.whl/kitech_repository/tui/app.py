"""
Main Textual TUI application for KITECH Repository Manager.

This is the entry point for the TUI, managing screen navigation and global state.
"""

import asyncio
import logging
from pathlib import Path

from textual.app import App

from kitech_repository.core.client import KitechClient
from kitech_repository.tui.messages import (
    FileOperationCompleted,
    FileOperationProgress,
    FileOperationStarted,
    RepositorySelected,
)
from kitech_repository.tui.models import OperationStatus
from kitech_repository.tui.screens.file_manager import FileManagerScreen
from kitech_repository.tui.screens.repository_selection import RepositorySelectionScreen

logger = logging.getLogger(__name__)


class KitechTUI(App):
    """
    Main Textual application for KITECH Repository Manager.

    Features:
    - Repository selection screen on startup
    - File manager screen for browsing and transferring files
    - Global keyboard shortcuts (Ctrl+C, Ctrl+Q to quit)
    - Screen navigation based on user actions
    """

    TITLE = "KITECH Repository Manager"

    # Load CSS from styles directory
    CSS_PATH = Path(__file__).parent / "styles" / "main.tcss"

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, client: KitechClient, initial_repo_id: int | None = None, **kwargs):
        """
        Initialize the TUI application.

        Args:
            client: KitechClient instance for API calls
            initial_repo_id: Optional repository ID to bypass selection screen
            **kwargs: Additional arguments passed to App
        """
        super().__init__(**kwargs)
        self.client = client
        self.initial_repo_id = initial_repo_id
        self.current_repository_id: int | None = None
        self.current_repository_name: str | None = None

        # Semaphore for limiting concurrent file operations (10 concurrent max per research.md)
        self._operation_semaphore = asyncio.Semaphore(10)

        # Track active operations
        self._active_operations: dict[str, asyncio.Task] = {}

    def on_mount(self) -> None:
        """
        Mount the initial screen when app starts.

        If initial_repo_id is provided, go directly to FileManagerScreen.
        Otherwise, show RepositorySelectionScreen.
        """
        if self.initial_repo_id:
            # Skip repository selection, go directly to file manager
            # Note: We don't have the repo name, so we'll use the ID as placeholder
            self.current_repository_id = self.initial_repo_id
            self.current_repository_name = f"Repository {self.initial_repo_id}"
            self.push_screen(
                FileManagerScreen(
                    client=self.client, repository_id=self.initial_repo_id, repository_name=self.current_repository_name
                )
            )
        else:
            # Show repository selection screen
            self.push_screen(RepositorySelectionScreen(client=self.client))

    def on_repository_selected(self, message: RepositorySelected) -> None:
        """
        Handle repository selection.

        When user selects a repository, transition to FileManagerScreen.

        Args:
            message: RepositorySelected message with repo ID and name
        """
        self.current_repository_id = message.repository_id
        self.current_repository_name = message.repository_name

        # Push file manager screen
        self.push_screen(
            FileManagerScreen(
                client=self.client, repository_id=message.repository_id, repository_name=message.repository_name
            )
        )

    def action_quit(self) -> None:
        """
        Handle quit action (Ctrl+C, Ctrl+Q).

        Exits the application.
        """
        self.exit()

    def on_resize(self, event) -> None:
        """
        Handle terminal resize events.

        Textual handles layout reflow automatically, but we ensure that
        async file operations continue without interruption (T068).

        Args:
            event: Resize event from Textual
        """
        # Log resize event for debugging
        logger.debug(f"Terminal resized to {event.size}")

        # Active operations continue running - no interruption needed
        # Textual's reactive system handles layout updates automatically

        # If there are active operations, they will continue
        if self._active_operations:
            logger.debug(f"Terminal resize occurred with {len(self._active_operations)} active operations")

    def on_file_operation_started(self, message: FileOperationStarted) -> None:
        """
        Handle file operation started message.

        Initiates async download/upload operation using KitechClient.
        Also relays to ProgressPanel for UI updates.

        Args:
            message: FileOperationStarted message with operation details
        """
        operation = message.operation
        logger.info("=== KitechTUI.on_file_operation_started CALLED ===")
        logger.info(f"Operation ID: {operation.operation_id}")
        logger.info(f"Operation type: {operation.operation_type}")
        logger.info(f"File path: {operation.file_path}")
        logger.info(f"Remote path: {operation.remote_path}")

        # Relay message to ProgressPanel
        try:
            from kitech_repository.tui.widgets.progress_panel import ProgressPanel

            logger.info("Looking for ProgressPanel...")
            for screen in self.screen_stack:
                if isinstance(screen, FileManagerScreen):
                    progress_panel = screen.query_one("#progress-panel", ProgressPanel)
                    logger.info("Found ProgressPanel, calling on_file_operation_started")
                    progress_panel.on_file_operation_started(message)
                    logger.info("ProgressPanel.on_file_operation_started called successfully")
                    break
        except Exception as e:
            logger.error(f"Failed to relay message to ProgressPanel: {e}", exc_info=True)

        # Create async task for the operation
        logger.info("Creating async task for operation...")
        task = asyncio.create_task(self._handle_file_operation(operation))
        self._active_operations[operation.operation_id] = task
        logger.info(f"Task created and stored. Total active operations: {len(self._active_operations)}")

    async def _handle_file_operation(self, operation) -> None:
        """
        Handle a file operation (download or upload).

        Args:
            operation: FileOperation model with operation details
        """
        try:
            logger.info(f"=== _handle_file_operation: Starting {operation.operation_type} ===")
            # Acquire semaphore to limit concurrency
            logger.info("Acquiring semaphore...")
            async with self._operation_semaphore:
                logger.info(f"Semaphore acquired. Operation type: {operation.operation_type}")
                if operation.operation_type == "download":
                    logger.info("Calling _handle_download_single...")
                    await self._handle_download_single(operation)
                elif operation.operation_type == "download_all":
                    logger.info("Calling _handle_download_all...")
                    await self._handle_download_all(operation)
                elif operation.operation_type == "upload":
                    logger.info("Calling _handle_upload_single...")
                    await self._handle_upload_single(operation)
                elif operation.operation_type == "upload_all":
                    logger.info("Calling _handle_upload_all (selected folder)...")
                    await self._handle_upload_all(operation, include_folder_name=True)
                elif operation.operation_type == "upload_current_dir":
                    logger.info("Calling _handle_upload_all (current directory contents)...")
                    await self._handle_upload_all(operation, include_folder_name=False)
                else:
                    raise ValueError(f"Unknown operation type: {operation.operation_type}")
            logger.info(f"=== _handle_file_operation: Completed {operation.operation_type} ===")

        except Exception as e:
            logger.error(f"=== Operation {operation.operation_id} FAILED: {e} ===", exc_info=True)
            self.post_message(FileOperationCompleted(operation_id=operation.operation_id, success=False, error=str(e)))
        finally:
            # Clean up task reference
            logger.info(f"Cleaning up operation {operation.operation_id}")
            self._active_operations.pop(operation.operation_id, None)

    async def _handle_download_single(self, operation) -> None:
        """
        Handle single file download.

        Downloads to the local panel's current directory path.

        Args:
            operation: FileOperation for download
        """
        logger.info(f"=== _handle_download_single: Starting download of {operation.remote_path} ===")

        # Post progress update (started)
        logger.info("Setting operation status to IN_PROGRESS and posting progress 0%")
        operation.status = OperationStatus.IN_PROGRESS
        progress_msg = FileOperationProgress(operation_id=operation.operation_id, progress_percent=0.0)
        self.post_message(progress_msg)
        self._relay_to_progress_panel_progress(progress_msg)
        logger.info("Posted FileOperationProgress message (0%)")

        # Get download directory from local panel's current path
        download_dir = self._get_local_panel_path()
        logger.info(f"Download directory: {download_dir}")

        # Download file (run in thread pool to avoid blocking)
        logger.info(f"Calling client.download_file with repo_id={self.current_repository_id}, path={operation.remote_path}")
        _output_path = await asyncio.to_thread(
            self.client.download_file,
            repository_id=self.current_repository_id,
            path=operation.remote_path,
            output_dir=download_dir,
            show_progress=False,  # We'll show progress in TUI
        )
        logger.info(f"Download completed successfully. Output path: {_output_path}")

        # Verify SHA-256 hash if available (T079)
        # Note: The client already verifies hashes internally during download
        # For additional verification, we could check the downloaded file here

        # Post progress update (completed)
        logger.info("Posting progress 100%")
        progress_msg = FileOperationProgress(operation_id=operation.operation_id, progress_percent=100.0)
        self.post_message(progress_msg)
        self._relay_to_progress_panel_progress(progress_msg)
        logger.info("Posted FileOperationProgress message (100%)")

        # Post completion message
        logger.info("Posting FileOperationCompleted message")
        completed_msg = FileOperationCompleted(operation_id=operation.operation_id, success=True, error=None)
        self.post_message(completed_msg)
        self._relay_to_progress_panel_completed(completed_msg)
        logger.info("=== _handle_download_single: Completed successfully ===")

    async def _handle_download_all(self, operation) -> None:
        """
        Handle batch download (all files in directory) with parallel processing and progress updates.

        Gets file list from /download API, then downloads each file individually with progress tracking.

        Args:
            operation: FileOperation for batch download
        """
        logger.info(f"=== _handle_download_all: Starting batch download from {operation.remote_path} ===")

        # Post preparing status (fetching file list from API)
        operation.status = OperationStatus.PREPARING
        progress_msg = FileOperationProgress(operation_id=operation.operation_id, progress_percent=0.0)
        self.post_message(progress_msg)
        self._relay_to_progress_panel_progress(progress_msg)
        logger.info("Posted PREPARING status - fetching file list from API...")

        # Get download directory from local panel's current path
        download_dir = self._get_local_panel_path()
        logger.info(f"Download directory: {download_dir}")

        # Get download info from API (returns file list) - this may take 10+ seconds for large repos
        logger.info("Getting download info from API...")
        download_info = await asyncio.to_thread(
            self.client.get_download_url,
            repository_id=self.current_repository_id,
            path=operation.remote_path,
        )
        logger.info("File list fetched successfully")

        # Now transition to IN_PROGRESS for actual downloads
        operation.status = OperationStatus.IN_PROGRESS
        progress_msg = FileOperationProgress(operation_id=operation.operation_id, progress_percent=0.0)
        self.post_message(progress_msg)
        self._relay_to_progress_panel_progress(progress_msg)
        logger.info("Status changed to IN_PROGRESS - starting downloads")

        # Check if this is a folder download with files array
        if isinstance(download_info, dict) and "files" in download_info:
            files = download_info["files"]
            logger.info(f"Found {len(files)} files to download")

            if not files:
                raise ValueError(f"No files found in directory: {operation.remote_path or 'root'}")

            # Set batch progress tracking
            self._set_batch_progress_tracking(len(files))

            # Download files in parallel with semaphore for concurrency control
            completed_count = 0
            semaphore = asyncio.Semaphore(5)  # Max 5 concurrent downloads

            async def download_single_file(file_index: int, file_info: dict) -> tuple[int, str, bool, str | None]:
                """Download a single file and return result."""
                nonlocal completed_count
                async with semaphore:
                    try:
                        file_name = file_info["name"]
                        file_path = file_info["path"]
                        logger.info(f"Downloading file {file_index}/{len(files)}: {file_name}")

                        # Update current file number for progress display
                        self._update_current_file_number(file_index, file_name)

                        # Download individual file
                        await asyncio.to_thread(
                            self.client.download_file,
                            repository_id=self.current_repository_id,
                            path=file_path,
                            output_dir=download_dir,
                            show_progress=False,
                        )

                        completed_count += 1
                        # Post progress update
                        progress = (completed_count / len(files)) * 100.0
                        progress_msg = FileOperationProgress(operation_id=operation.operation_id, progress_percent=progress)
                        self.post_message(progress_msg)
                        self._relay_to_progress_panel_progress(progress_msg)
                        logger.info(f"Download progress: {progress:.1f}%")

                        return (file_index, file_name, True, None)
                    except Exception as e:
                        logger.error(f"Failed to download {file_name}: {e}")
                        return (file_index, file_name, False, str(e))

            # Create tasks for all files
            tasks = [download_single_file(idx, f) for idx, f in enumerate(files, start=1)]

            # Execute all downloads in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and check for errors
            failed_downloads = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Download task raised exception: {result}")
                    failed_downloads.append(str(result))
                elif not result[2]:  # result[2] is the success boolean
                    logger.error(f"Download failed for {result[1]}: {result[3]}")
                    failed_downloads.append(f"{result[1]}: {result[3]}")

            # Clear batch tracking
            self._clear_batch_progress_tracking()

            # Post completion message with error info if any failed
            if failed_downloads:
                error_msg = f"Failed to download {len(failed_downloads)} file(s): " + "; ".join(failed_downloads[:3])
                if len(failed_downloads) > 3:
                    error_msg += f" (and {len(failed_downloads) - 3} more)"
                logger.error(f"Download batch completed with errors: {error_msg}")
                completed_msg = FileOperationCompleted(operation_id=operation.operation_id, success=False, error=error_msg)
            else:
                logger.info("All downloads completed successfully")
                completed_msg = FileOperationCompleted(operation_id=operation.operation_id, success=True, error=None)

            self.post_message(completed_msg)
            self._relay_to_progress_panel_completed(completed_msg)
            logger.info("=== _handle_download_all: Completed ===")
        else:
            # Fallback: single file or unexpected response
            logger.warning("Unexpected download_info format, using fallback method")
            await asyncio.to_thread(
                self.client.download_file,
                repository_id=self.current_repository_id,
                path=operation.remote_path,
                output_dir=download_dir,
                show_progress=False,
                is_directory=True,
            )

            # Post completion
            progress_msg = FileOperationProgress(operation_id=operation.operation_id, progress_percent=100.0)
            self.post_message(progress_msg)
            self._relay_to_progress_panel_progress(progress_msg)

            completed_msg = FileOperationCompleted(operation_id=operation.operation_id, success=True, error=None)
            self.post_message(completed_msg)
            self._relay_to_progress_panel_completed(completed_msg)
            logger.info("=== _handle_download_all: Completed (fallback) ===")

    async def _handle_upload_single(self, operation) -> None:
        """
        Handle single file upload.

        Args:
            operation: FileOperation for upload
        """
        logger.info(f"=== _handle_upload_single: Starting upload of {operation.local_path} ===")

        # Post progress update (started)
        logger.info("Setting operation status to IN_PROGRESS and posting progress 0%")
        operation.status = OperationStatus.IN_PROGRESS
        progress_msg = FileOperationProgress(operation_id=operation.operation_id, progress_percent=0.0)
        self.post_message(progress_msg)
        self._relay_to_progress_panel_progress(progress_msg)
        logger.info("Posted FileOperationProgress message (0%)")

        # Calculate MD5 hash (T080) - done by client.upload_file internally
        # Upload file (run in thread pool)
        logger.info(f"Calling client.upload_file with repo_id={self.current_repository_id}, file_path={operation.local_path}")
        _result = await asyncio.to_thread(
            self.client.upload_file,
            repository_id=self.current_repository_id,
            file_path=Path(operation.local_path),
            remote_path=operation.remote_path or "",
            show_progress=False,  # We'll show progress in TUI
        )
        logger.info(f"Upload completed successfully")

        # Post progress update (completed)
        logger.info("Posting progress 100%")
        progress_msg = FileOperationProgress(operation_id=operation.operation_id, progress_percent=100.0)
        self.post_message(progress_msg)
        self._relay_to_progress_panel_progress(progress_msg)
        logger.info("Posted FileOperationProgress message (100%)")

        # Post completion message
        logger.info("Posting FileOperationCompleted message")
        completed_msg = FileOperationCompleted(operation_id=operation.operation_id, success=True, error=None)
        self.post_message(completed_msg)
        self._relay_to_progress_panel_completed(completed_msg)
        logger.info("=== _handle_upload_single: Completed successfully ===")

    async def _handle_upload_all(self, operation, include_folder_name: bool = True) -> None:
        """
        Handle batch upload (all files in directory).

        Includes progress tracking for multiple files (T067).

        Args:
            operation: FileOperation for batch upload
            include_folder_name: If True, include folder name in remote path (F4).
                                 If False, upload contents only (F3).
        """
        logger.info(f"=== _handle_upload_all: Starting batch upload from {operation.local_path} ===")

        # Post preparing status (scanning local directory for files)
        operation.status = OperationStatus.PREPARING
        progress_msg = FileOperationProgress(operation_id=operation.operation_id, progress_percent=0.0)
        self.post_message(progress_msg)
        self._relay_to_progress_panel_progress(progress_msg)
        logger.info("Posted PREPARING status - scanning local directory...")

        # Get all files in directory
        local_path = Path(operation.local_path)
        if not local_path.is_dir():
            raise ValueError(f"Path is not a directory: {local_path}")

        # Get all files recursively to preserve folder structure
        files = [f for f in local_path.rglob("*") if f.is_file()]

        if not files:
            raise ValueError(f"No files found in directory: {local_path}")

        logger.info(f"Found {len(files)} files to upload")

        # Now transition to IN_PROGRESS for actual uploads
        operation.status = OperationStatus.IN_PROGRESS
        progress_msg = FileOperationProgress(operation_id=operation.operation_id, progress_percent=0.0)
        self.post_message(progress_msg)
        self._relay_to_progress_panel_progress(progress_msg)
        logger.info("Status changed to IN_PROGRESS - starting uploads")

        # Set batch progress tracking (T067)
        self._set_batch_progress_tracking(len(files))

        # Upload files in parallel with semaphore for concurrency control
        completed_count = 0
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent uploads

        async def upload_single_file(file_index: int, file_path: Path) -> tuple[int, Path, bool, str | None]:
            """Upload a single file and return result."""
            nonlocal completed_count
            async with semaphore:
                try:
                    logger.info(f"Uploading file {file_index}/{len(files)}: {file_path.name}")
                    # Update current file number for progress display
                    self._update_current_file_number(file_index, file_path.name)

                    # Calculate relative path to preserve folder structure
                    relative_path = file_path.relative_to(local_path)

                    if include_folder_name:
                        # F4: Include selected folder name in path
                        folder_name = local_path.name
                        if relative_path.parent != Path("."):
                            remote_file_path = f"{folder_name}/{relative_path.parent}/"
                        else:
                            remote_file_path = f"{folder_name}/"
                        logger.info(f"Uploading to: '{remote_file_path}' (with folder: {folder_name})")
                    else:
                        # F3: Upload directory contents only (no folder name prefix)
                        if relative_path.parent != Path("."):
                            remote_file_path = f"{relative_path.parent}/"
                        else:
                            remote_file_path = ""
                        logger.info(f"Uploading to: '{remote_file_path}' (contents only)")

                    await asyncio.to_thread(
                        self.client.upload_file,
                        repository_id=self.current_repository_id,
                        file_path=file_path,
                        remote_path=remote_file_path,
                        show_progress=False,
                    )

                    completed_count += 1
                    # Post progress update
                    progress = (completed_count / len(files)) * 100.0
                    progress_msg = FileOperationProgress(operation_id=operation.operation_id, progress_percent=progress)
                    self.post_message(progress_msg)
                    self._relay_to_progress_panel_progress(progress_msg)
                    logger.info(f"Upload progress: {progress:.1f}%")

                    return (file_index, file_path, True, None)
                except Exception as e:
                    logger.error(f"Failed to upload {file_path.name}: {e}")
                    return (file_index, file_path, False, str(e))

        # Create tasks for all files
        tasks = [upload_single_file(idx, fp) for idx, fp in enumerate(files, start=1)]

        # Execute all uploads in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and check for errors
        failed_uploads = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Upload task raised exception: {result}")
                failed_uploads.append(str(result))
            elif not result[2]:  # result[2] is the success boolean
                logger.error(f"Upload failed for {result[1].name}: {result[3]}")
                failed_uploads.append(f"{result[1].name}: {result[3]}")

        # Clear batch tracking
        self._clear_batch_progress_tracking()

        # Post completion message with error info if any failed
        if failed_uploads:
            error_msg = f"Failed to upload {len(failed_uploads)} file(s): " + "; ".join(failed_uploads[:3])
            if len(failed_uploads) > 3:
                error_msg += f" (and {len(failed_uploads) - 3} more)"
            logger.error(f"Upload batch completed with errors: {error_msg}")
            completed_msg = FileOperationCompleted(operation_id=operation.operation_id, success=False, error=error_msg)
        else:
            logger.info("All uploads completed successfully")
            completed_msg = FileOperationCompleted(operation_id=operation.operation_id, success=True, error=None)

        self.post_message(completed_msg)
        self._relay_to_progress_panel_completed(completed_msg)
        logger.info("=== _handle_upload_all: Completed ===")

    def _set_batch_progress_tracking(self, total_files: int) -> None:
        """
        Set up batch progress tracking for multiple file operations (T067).

        Args:
            total_files: Total number of files in the batch operation
        """
        try:
            from kitech_repository.tui.widgets.progress_panel import ProgressPanel

            # Find the active FileManagerScreen
            for screen in self.screen_stack:
                if isinstance(screen, FileManagerScreen):
                    progress_panel = screen.query_one("#progress-panel", ProgressPanel)
                    progress_panel.total_files = total_files
                    progress_panel.current_file_number = 0
                    break
        except Exception as e:
            logger.debug(f"Could not set batch progress tracking: {e}")

    def _update_current_file_number(self, file_number: int, file_name: str) -> None:
        """
        Update the current file number in batch progress tracking (T067).

        Args:
            file_number: Current file number (1-indexed)
            file_name: Name of the current file being processed
        """
        try:
            from kitech_repository.tui.widgets.progress_panel import ProgressPanel

            # Find the active FileManagerScreen
            for screen in self.screen_stack:
                if isinstance(screen, FileManagerScreen):
                    progress_panel = screen.query_one("#progress-panel", ProgressPanel)
                    progress_panel.current_file_number = file_number
                    # Force update of progress display
                    if progress_panel.current_operation:
                        progress_panel.current_operation.file_path = file_name
                        progress_panel._update_progress_display(progress_panel.current_operation)
                    break
        except Exception as e:
            logger.debug(f"Could not update current file number: {e}")

    def _clear_batch_progress_tracking(self) -> None:
        """
        Clear batch progress tracking after operation completes (T067).
        """
        try:
            from kitech_repository.tui.widgets.progress_panel import ProgressPanel

            # Find the active FileManagerScreen
            for screen in self.screen_stack:
                if isinstance(screen, FileManagerScreen):
                    progress_panel = screen.query_one("#progress-panel", ProgressPanel)
                    progress_panel.total_files = 0
                    progress_panel.current_file_number = 0
                    break
        except Exception as e:
            logger.debug(f"Could not clear batch progress tracking: {e}")

    def _get_local_panel_path(self) -> Path:
        """
        Get the current path from the local panel.

        Returns the local panel's current directory path for download operations.
        Falls back to ~/Downloads if unable to read the panel path.

        Returns:
            Path: Current local panel directory path
        """
        try:
            from kitech_repository.tui.widgets.local_panel import LocalPanel

            # Find the active FileManagerScreen
            for screen in self.screen_stack:
                if isinstance(screen, FileManagerScreen):
                    local_panel = screen.query_one("#local-panel", LocalPanel)
                    return local_panel.current_path
        except Exception as e:
            logger.debug(f"Could not get local panel path: {e}")

        # Fallback to Downloads directory
        return Path.home() / "Downloads"

    def _relay_to_progress_panel_progress(self, message: FileOperationProgress) -> None:
        """Relay progress message to ProgressPanel."""
        try:
            from kitech_repository.tui.widgets.progress_panel import ProgressPanel

            for screen in self.screen_stack:
                if isinstance(screen, FileManagerScreen):
                    progress_panel = screen.query_one("#progress-panel", ProgressPanel)
                    progress_panel.on_file_operation_progress(message)
                    break
        except Exception as e:
            logger.debug(f"Could not relay progress to ProgressPanel: {e}")

    def _relay_to_progress_panel_completed(self, message: FileOperationCompleted) -> None:
        """Relay completed message to ProgressPanel, LocalPanel, and RemotePanel for auto-refresh."""
        logger.info("=== _relay_to_progress_panel_completed CALLED ===")
        logger.info(f"Message operation_id: {message.operation_id}, success: {message.success}")

        try:
            from kitech_repository.tui.widgets.progress_panel import ProgressPanel
            from kitech_repository.tui.widgets.local_panel import LocalPanel
            from kitech_repository.tui.widgets.remote_panel import RemotePanel

            logger.info(f"Screen stack count: {len(self.screen_stack)}")

            for screen in self.screen_stack:
                logger.info(f"Checking screen: {type(screen).__name__}")
                if isinstance(screen, FileManagerScreen):
                    logger.info("Found FileManagerScreen, relaying to panels...")

                    # Clear the global operation active flag FIRST
                    screen.is_operation_active = False
                    logger.info("Cleared FileManagerScreen.is_operation_active flag")

                    # Relay to ProgressPanel
                    progress_panel = screen.query_one("#progress-panel", ProgressPanel)
                    progress_panel.on_file_operation_completed(message)
                    logger.info("Relayed completed message to ProgressPanel")

                    # Relay to LocalPanel for auto-refresh
                    try:
                        local_panel = screen.query_one("#local-panel", LocalPanel)
                        local_panel.on_file_operation_completed(message)
                        logger.info("Relayed completed message to LocalPanel")
                    except Exception as e:
                        logger.error(f"Failed to relay to LocalPanel: {e}", exc_info=True)

                    # Relay to RemotePanel for auto-refresh
                    try:
                        remote_panel = screen.query_one("#remote-panel", RemotePanel)
                        remote_panel.on_file_operation_completed(message)
                        logger.info("Relayed completed message to RemotePanel")
                    except Exception as e:
                        logger.error(f"Failed to relay to RemotePanel: {e}", exc_info=True)

                    break
        except Exception as e:
            logger.error(f"Could not relay completed message: {e}", exc_info=True)
