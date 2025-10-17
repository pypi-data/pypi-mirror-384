"""
Confirmation dialog widget for destructive operations.

This modal dialog prompts the user to confirm or cancel an action
using keyboard input (Y/N).
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmationDialog(ModalScreen):
    """
    Modal confirmation dialog with Y/N keyboard input.

    Features:
    - Displays a confirmation message
    - Y key or Enter to confirm
    - N key or Escape to cancel
    - Buttons for mouse users
    """

    BINDINGS = [
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
        ("enter", "confirm", "Confirm"),
        ("escape", "cancel", "Cancel"),
    ]

    CSS = """
    ConfirmationDialog {
        align: center middle;
    }

    ConfirmationDialog > Container {
        width: 60;
        height: auto;
        background: #222222;
        border: heavy yellow;
        padding: 1;
    }

    ConfirmationDialog Label {
        width: 100%;
        content-align: center middle;
        padding: 1;
    }

    ConfirmationDialog .button-container {
        layout: horizontal;
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1;
    }

    ConfirmationDialog Button {
        margin: 0 1;
    }
    """

    def __init__(self, message: str, **kwargs):
        """
        Initialize the confirmation dialog.

        Args:
            message: The confirmation message to display
            **kwargs: Additional arguments passed to ModalScreen
        """
        super().__init__(**kwargs)
        self.message = message

    def compose(self) -> ComposeResult:
        """Compose the dialog UI."""
        with Container():
            yield Label(self.message)
            with Vertical(classes="button-container"):
                yield Button("Yes (Y)", id="confirm-button", variant="success")
                yield Button("No (N)", id="cancel-button", variant="error")

    def action_confirm(self) -> None:
        """Handle confirmation action (Y key or Enter)."""
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Handle cancel action (N key or Escape)."""
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle button press events.

        Args:
            event: Button.Pressed event
        """
        if event.button.id == "confirm-button":
            self.action_confirm()
        elif event.button.id == "cancel-button":
            self.action_cancel()
