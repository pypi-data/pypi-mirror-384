"""
File manager screen for KITECH TUI.

This screen displays a dual-panel interface with local and remote file panels,
allowing users to navigate, upload, and download files.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header

from kitech_repository.core.client import KitechClient
from kitech_repository.tui.messages import (
    FileOperationCompleted,
    FileOperationProgress,
    FileOperationStarted,
    PanelFocusChanged,
)
from kitech_repository.tui.models import PanelType
from kitech_repository.tui.widgets.local_panel import LocalPanel
from kitech_repository.tui.widgets.progress_panel import ProgressPanel
from kitech_repository.tui.widgets.remote_panel import RemotePanel


class FileManagerScreen(Screen):
    """
    Dual-panel file manager screen.

    Features:
    - LocalPanel for browsing local filesystem
    - RemotePanel for browsing remote repository files
    - Tab key switches focus between panels
    - Footer shows context-sensitive keyboard shortcuts
    - ProgressPanel shows file operation progress
    - Q/Escape returns to repository selection
    """

    BINDINGS = [
        ("tab", "switch_panel", "Switch Panel"),
        ("q", "quit_to_repos", "Back to Repos"),
        ("escape", "quit_to_repos", "Back to Repos"),
    ]

    CSS = """
    FileManagerScreen {
        layout: vertical;
    }

    FileManagerScreen Horizontal {
        height: 1fr;
        layout: horizontal;
    }

    FileManagerScreen LocalPanel {
        width: 1fr;
    }

    FileManagerScreen RemotePanel {
        width: 1fr;
    }

    FileManagerScreen ProgressPanel {
        height: auto;
    }
    """

    def __init__(self, client: KitechClient, repository_id: int, repository_name: str, **kwargs):
        """
        Initialize the file manager screen.

        Args:
            client: KitechClient instance for API calls
            repository_id: ID of the repository to browse
            repository_name: Name of the repository
            **kwargs: Additional arguments passed to Screen
        """
        super().__init__(**kwargs)
        self.client = client
        self.repository_id = repository_id
        self.repository_name = repository_name
        self._focused_panel = PanelType.REMOTE  # Start with remote panel focused per spec FR-023
        self.is_operation_active = False  # Global flag for any file operation (upload or download)

    def compose(self) -> ComposeResult:
        """Compose the file manager screen UI."""
        yield Header()

        # Dual-panel layout
        with Horizontal():
            yield LocalPanel(id="local-panel", classes="panel")
            yield RemotePanel(
                client=self.client,
                repository_id=self.repository_id,
                repository_name=self.repository_name,
                id="remote-panel",
                classes="panel",
            )

        # Progress panel (hidden by default)
        yield ProgressPanel(id="progress-panel")

        yield Footer()

    def on_mount(self) -> None:
        """Set initial focus when screen mounts."""
        # Per spec FR-023: remote panel should have initial focus
        remote_panel = self.query_one("#remote-panel", RemotePanel)
        local_panel = self.query_one("#local-panel", LocalPanel)

        remote_panel.has_focus = True
        local_panel.has_focus = False

    def action_switch_panel(self) -> None:
        """
        Handle Tab key to switch focus between panels.

        Toggles focus between LocalPanel and RemotePanel, and moves
        the DataTable cursor to the focused panel.
        """
        local_panel = self.query_one("#local-panel", LocalPanel)
        remote_panel = self.query_one("#remote-panel", RemotePanel)

        if self._focused_panel == PanelType.LOCAL:
            # Switch to remote
            local_panel.has_focus = False
            remote_panel.has_focus = True
            self._focused_panel = PanelType.REMOTE

            # Move focus to remote table widget to move cursor
            try:
                remote_table = remote_panel.query_one("#remote-table")
                remote_table.focus()
            except Exception:
                pass  # Table might not be mounted yet
        else:
            # Switch to local
            remote_panel.has_focus = False
            local_panel.has_focus = True
            self._focused_panel = PanelType.LOCAL

            # Move focus to local table widget to move cursor
            try:
                local_table = local_panel.query_one("#local-table")
                local_table.focus()
            except Exception:
                pass  # Table might not be mounted yet

        # Post message for any listeners
        self.post_message(PanelFocusChanged(panel_type=self._focused_panel))

    def action_quit_to_repos(self) -> None:
        """
        Handle quit action (Q/Escape keys).

        Returns to repository selection screen.
        """
        # This will be handled by the main app
        # which will pop this screen and show repository selection
        self.dismiss()

    def watch_focused_panel(self, old: PanelType, new: PanelType) -> None:
        """
        React to focused panel changes.

        Updates Footer with context-sensitive keyboard shortcuts.

        Args:
            old: Previous focused panel
            new: New focused panel
        """
        # Footer binding updates will be automatic via BINDINGS on panels
        # The Footer widget reads BINDINGS from focused widgets
        pass

    def on_file_operation_started(self, message: FileOperationStarted) -> None:
        """
        Handle file operation started message and relay to ProgressPanel.

        Since Textual messages bubble UP the widget tree, ProgressPanel (a child)
        won't receive the message unless we explicitly relay it.

        Args:
            message: FileOperationStarted message with operation details
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info("=== FileManagerScreen.on_file_operation_started CALLED ===")
        logger.info(f"Relaying message to ProgressPanel...")

        # Set global operation active flag
        self.is_operation_active = True
        logger.info("Global is_operation_active flag set to True")

        progress_panel = self.query_one("#progress-panel", ProgressPanel)
        # Explicitly call ProgressPanel's handler
        progress_panel.on_file_operation_started(message)
        logger.info("Message relayed to ProgressPanel")

    def on_file_operation_progress(self, message: FileOperationProgress) -> None:
        """
        Handle file operation progress message and relay to ProgressPanel.

        Args:
            message: FileOperationProgress message with progress update
        """
        progress_panel = self.query_one("#progress-panel", ProgressPanel)
        progress_panel.on_file_operation_progress(message)

    def on_file_operation_completed(self, message: FileOperationCompleted) -> None:
        """
        Handle file operation completed message and relay to panels.

        Relays to ProgressPanel, LocalPanel, and RemotePanel for auto-refresh.

        Args:
            message: FileOperationCompleted message with success/error status
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info("=== FileManagerScreen.on_file_operation_completed CALLED ===")

        # Clear global operation active flag
        self.is_operation_active = False
        logger.info("Global is_operation_active flag set to False")

        # Relay to ProgressPanel
        progress_panel = self.query_one("#progress-panel", ProgressPanel)
        progress_panel.on_file_operation_completed(message)
        logger.info("Message relayed to ProgressPanel")

        # Relay to LocalPanel for auto-refresh
        try:
            local_panel = self.query_one("#local-panel", LocalPanel)
            local_panel.on_file_operation_completed(message)
            logger.info("Message relayed to LocalPanel")
        except Exception as e:
            logger.error(f"Failed to relay to LocalPanel: {e}")

        # Relay to RemotePanel for auto-refresh
        try:
            remote_panel = self.query_one("#remote-panel", RemotePanel)
            remote_panel.on_file_operation_completed(message)
            logger.info("Message relayed to RemotePanel")
        except Exception as e:
            logger.error(f"Failed to relay to RemotePanel: {e}")
