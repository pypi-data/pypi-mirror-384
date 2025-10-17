"""
Repository selection screen for KITECH TUI.

This screen displays a list of accessible repositories and allows the user
to select one for file management operations.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, LoadingIndicator, Static

from kitech_repository.core.client import KitechClient
from kitech_repository.core.exceptions import ApiError, AuthenticationError
from kitech_repository.tui.messages import RepositorySelected


class RepositorySelectionScreen(Screen):
    """
    Screen for selecting a repository from the user's accessible repositories.

    Features:
    - Loads repository list from API on mount
    - Displays repositories in a DataTable with Name and Owner columns
    - Allows selection with Enter key
    - Supports refresh with F5
    - Handles empty list and error states
    """

    BINDINGS = [
        ("f5", "refresh", "Refresh List"),
        ("escape", "quit_app", "Quit"),
    ]

    CSS = """
    RepositorySelectionScreen {
        align: center middle;
    }

    #repository-table {
        width: 80%;
        height: 70%;
        margin: 2 4;
    }

    #empty-message, #error-message {
        width: 80%;
        height: auto;
        margin: 2 4;
        text-align: center;
    }

    #loading-container {
        width: 80%;
        height: auto;
        margin: 2 4;
        align: center middle;
    }

    #loading-message {
        text-align: center;
        color: yellow;
        margin: 1 0;
    }

    LoadingIndicator {
        height: auto;
        margin: 1 0;
    }
    """

    def __init__(self, client: KitechClient, **kwargs):
        """
        Initialize the repository selection screen.

        Args:
            client: KitechClient instance for API calls
            **kwargs: Additional arguments passed to Screen
        """
        super().__init__(**kwargs)
        self.client = client
        self._repositories = []
        self._loading = False

    def compose(self) -> ComposeResult:
        """Compose the repository selection screen UI."""
        yield Header()
        yield Container(id="content-container")
        yield Footer()

    async def on_mount(self) -> None:
        """Load repositories from API when screen mounts."""
        await self._load_repositories()

    async def _load_repositories(self) -> None:
        """
        Load repository list from API and populate the DataTable.

        Handles success, empty list, and error cases with loading indicators
        and actionable error messages (T062, T064).
        """
        self._loading = True
        container = self.query_one("#content-container", Container)

        # Clear existing content
        await container.remove_children()

        # Show loading indicator with message (T062)
        loading_container = Vertical(id="loading-container")
        await container.mount(loading_container)
        await loading_container.mount(LoadingIndicator())
        await loading_container.mount(Static("Loading repositories...", id="loading-message"))

        try:
            # Call API to get repositories (synchronous call, returns dict)
            result = self.client.list_repositories()
            repositories = result.get("repositories", [])
            self._repositories = repositories

            # Remove loading indicator
            await container.remove_children()

            if not repositories:
                # Empty state
                await container.mount(
                    Static(
                        "No repositories accessible\n\n"
                        "You don't have access to any repositories.\n"
                        "Contact your administrator to request access.\n\n"
                        "Press F5 to refresh or Escape to quit.",
                        id="empty-message",
                        classes="status-warning",
                    )
                )
            else:
                # Create and populate DataTable
                table = DataTable(id="repository-table")
                table.cursor_type = "row"
                table.zebra_stripes = True

                # Add columns
                table.add_column("Name", key="name")
                table.add_column("Owner", key="owner")
                table.add_column("Description", key="description")

                # Add rows
                for repo in repositories:
                    table.add_row(repo.name, repo.owner_name, repo.description or "", key=str(repo.id))

                await container.mount(table)

                # Focus the table
                table.focus()

        except AuthenticationError as e:
            # Authentication error - specific actionable message (T064)
            await container.remove_children()
            await container.mount(
                Static(
                    f"Authentication Failed\n\n"
                    f"Your session may have expired or your API key is invalid.\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Action: Run 'kitech-dev login' to re-authenticate.\n"
                    f"Press Escape to quit.",
                    id="error-message",
                    classes="status-error",
                )
            )
        except ApiError as e:
            # API/Network error - actionable message with retry instruction (T064)
            await container.remove_children()
            await container.mount(
                Static(
                    f"Network Error\n\n"
                    f"Failed to connect to the repository server.\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Action: Check your network connection and press F5 to retry.\n"
                    f"Press Escape to quit.",
                    id="error-message",
                    classes="status-error",
                )
            )
        except Exception as e:
            # Generic error - actionable message (T064)
            await container.remove_children()
            await container.mount(
                Static(
                    f"Failed to load repositories\n\n"
                    f"An unexpected error occurred.\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Action: Press F5 to retry or Escape to quit.",
                    id="error-message",
                    classes="status-error",
                )
            )

        finally:
            self._loading = False

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """
        Handle repository selection when user presses Enter on a row.

        This is called automatically by Textual when Enter is pressed on a DataTable row.

        Args:
            event: The RowSelected event from DataTable
        """
        # Row key is the repository ID (we set it as str(repo.id) when adding rows)
        try:
            repo_id = int(event.row_key.value)  # Convert RowKey to int
        except (ValueError, AttributeError):
            return

        # Find the repository by ID
        selected_repo = None
        for repo in self._repositories:
            if repo.id == repo_id:
                selected_repo = repo
                break

        if selected_repo:
            # Post RepositorySelected message
            self.post_message(RepositorySelected(repository_id=selected_repo.id, repository_name=selected_repo.name))

    async def action_refresh(self) -> None:
        """
        Handle refresh action (F5 key).

        Reloads the repository list from the API.
        """
        if not self._loading:
            await self._load_repositories()

    def action_quit_app(self) -> None:
        """
        Handle quit action (Escape key).

        Exits the application.
        """
        self.app.exit()
