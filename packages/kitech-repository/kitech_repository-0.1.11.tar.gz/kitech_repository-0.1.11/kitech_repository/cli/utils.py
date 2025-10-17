"""Utility functions for CLI."""

import sys
from pathlib import Path


def get_cli_command_name() -> str:
    """
    Get the CLI command name that was used to invoke this script.

    Returns:
        str: The command name (e.g., 'kitech-dev', 'kitech')

    Examples:
        >>> # When invoked as: kitech-dev auth login
        >>> get_cli_command_name()
        'kitech-dev'

        >>> # When invoked as: kitech manager start
        >>> get_cli_command_name()
        'kitech'
    """
    # Get the command that was used to invoke this script
    argv0 = sys.argv[0]

    # Extract just the command name from the path
    # e.g., /path/to/kitech-dev -> kitech-dev
    command_name = Path(argv0).stem

    # If the command is 'python' or 'python3' or similar, use a default
    if command_name.startswith('python'):
        # Fallback to 'kitech-dev' for development
        return 'kitech-dev'

    return command_name
