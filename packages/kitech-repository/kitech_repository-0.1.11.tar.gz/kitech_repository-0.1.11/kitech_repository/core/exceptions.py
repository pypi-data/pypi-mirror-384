"""Exception definitions for KITECH Repository."""

from pathlib import Path


class KitechException(Exception):
    """Base exception for KITECH Repository."""

    pass


class AuthenticationError(KitechException):
    """Authentication related errors."""

    pass


class ApiError(KitechException):
    """API request related errors."""

    pass


class DownloadError(KitechException):
    """File download related errors."""

    pass


class BatchDownloadError(DownloadError):
    """Batch download partial or complete failure.

    Raised when one or more files fail to download in a batch operation.
    Contains information about both successful and failed downloads.

    Attributes:
        successful: List of successfully downloaded file paths
        failed: List of FailedDownload objects with error details
        message: Error message summary

    Example:
        >>> try:
        ...     files = await client.download_batch(repo_id, paths)
        ... except BatchDownloadError as e:
        ...     print(f"Failed: {e.failure_count}/{e.total_count}")
        ...     for failure in e.failed:
        ...         print(f"  {failure.name}: {failure.error}")
        ...     # Process successful downloads anyway
        ...     for file in e.successful:
        ...         process(file)
    """

    def __init__(self, successful: list[Path], failed: list, message: str | None = None):
        """Initialize BatchDownloadError.

        Args:
            successful: List of successfully downloaded Paths
            failed: List of FailedDownload objects
            message: Optional custom error message
        """
        self.successful = successful
        self.failed = failed

        if message is None:
            message = f"Batch download failed: {len(failed)}/{len(successful) + len(failed)} files failed"

        super().__init__(message)

    @property
    def total_count(self) -> int:
        """Total number of attempted downloads."""
        return len(self.successful) + len(self.failed)

    @property
    def success_count(self) -> int:
        """Number of successful downloads."""
        return len(self.successful)

    @property
    def failure_count(self) -> int:
        """Number of failed downloads."""
        return len(self.failed)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage (0-100)."""
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100


class UploadError(KitechException):
    """File upload related errors."""

    pass


class ConfigurationError(KitechException):
    """Configuration related errors."""

    pass
