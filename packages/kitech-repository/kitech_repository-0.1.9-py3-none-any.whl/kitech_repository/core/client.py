"""Main client for KITECH Repository API."""

import asyncio
import hashlib
import logging
import tempfile
import zipfile
from pathlib import Path

import httpx
from tqdm import tqdm

from kitech_repository.core.auth import AuthManager
from kitech_repository.core.config import Config
from kitech_repository.core.exceptions import (
    ApiError,
    AuthenticationError,
    BatchDownloadError,
    DownloadError,
    UploadError,
)
from kitech_repository.core.zip_utils import ZipExtractor, ZipSecurityValidator
from kitech_repository.models.file import (
    BatchDownloadResult,
    FailedDownload,
    File,
    FileDownloadInfo,
)
from kitech_repository.models.repository import Repository

logger = logging.getLogger(__name__)


class KitechClient:
    """Main client for interacting with KITECH Repository API."""

    def __init__(
        self,
        config: Config | None = None,
        token: str | None = None,
        api_version: str = "v1",
    ):
        """Initialize KITECH client.

        Args:
            config: Configuration object. If not provided, loads from Config.load()
            token: API token. If provided, will login with this token
            api_version: API version (default: "v1"). Use empty string for no version.
        """
        self.config = config or Config.load()
        self.api_version = api_version
        self.auth_manager = AuthManager(self.config)

        # Use provided token if available
        if token:
            self.auth_manager.login(app_key=token)

        # Construct base_url dynamically with version
        base_url = (
            f"{self.config.api_base_url}/{api_version}"
            if api_version
            else self.config.api_base_url
        )

        self.client = httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(600.0, connect=30.0),  # 10 minutes total, 30s connect
            headers=(
                self.auth_manager.headers
                if self.auth_manager.is_authenticated()
                else {}
            ),
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self._close()

    def _close(self):
        """Close the HTTP client."""
        self.client.close()

    def close(self):
        """Close the HTTP client (public API)."""
        self._close()

    def test_connection(self) -> dict:
        """Test connection and authentication to the API."""
        try:
            response = self.client.get("/cli/test")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid or expired API token") from e
            raise ApiError(f"API request failed: {e}") from e
        except Exception as e:
            raise ApiError(f"Connection test failed: {e}") from e

    def list_repositories(
        self, page: int = 0, limit: int = 20, include_shared: bool = True
    ) -> dict[str, list[Repository]]:
        """List available repositories."""
        params = {
            "page": page,
            "limit": limit,
            "includeShared": include_shared,
        }

        try:
            response = self.client.get("/cli/repositories", params=params)
            response.raise_for_status()
            data = response.json()

            repositories = [Repository(**repo) for repo in data.get("repositories", [])]

            return {
                "repositories": repositories,
                "total_count": data.get("totalCount", 0),
            }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid or expired API token") from e
            raise ApiError(f"Failed to list repositories: {e}") from e

    def list_files(
        self,
        repository_id: int,
        prefix: str = "",
        search: str | None = None,
        include_hash: bool = False,
        limit: int = 100,
        page: int = 0,
    ) -> dict[str, list[File]]:
        """List files in a repository."""
        params = {"limit": limit, "page": page}
        if prefix:
            params["prefix"] = prefix
        if search:
            params["search"] = search
        if include_hash:
            params["includeHash"] = include_hash

        try:
            # Try new API endpoint first: /cli/repositories/{id}/files
            response = self.client.get(
                f"/cli/repositories/{repository_id}/files", params=params
            )
            response.raise_for_status()
            data = response.json()

            # Handle different API response structures
            if "files" in data:
                # Real API structure: {"files": [...], "totalCount": ..., "repositoryId": ...}
                files = [File(**file_data) for file_data in data.get("files", [])]
                total_count = data.get("totalCount", len(files))
                has_more = False  # Real API doesn't provide pagination info
            elif "content" in data:
                # Mock API structure: {"content": [...], "meta": {...}}
                content = data.get("content", [])
                meta = data.get("meta", {})
                files = [File(**file_data) for file_data in content]
                total_count = meta.get("total", len(files))
                has_more = (
                    meta.get("page", 0) < meta.get("maxPage", 0) - 1
                    if "maxPage" in meta
                    else False
                )
            else:
                files = []
                total_count = 0
                has_more = False

            return {
                "files": files,
                "repository_id": repository_id,
                "prefix": prefix,
                "total_count": total_count,
                "has_more": has_more,
                "page": page,
                "limit": limit,
            }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid or expired API token") from e
            elif e.response.status_code == 404:
                raise ApiError(f"Repository {repository_id} not found") from e
            raise ApiError(f"Failed to list files: {e}") from e

    def get_download_url(
        self, repository_id: int, path: str | None = None
    ) -> str | dict:
        """Get download URL for a file or folder.

        Args:
            repository_id: Repository ID
            path: Path to file/folder. None = download entire repository (no path parameter sent)

        Returns:
            For single file: dict with url, sha256, md5, path
            For folder: dict with files array containing each file's download info
            For backward compatibility: may return URL string for old API
        """
        params = {}
        # IMPORTANT: When path is None (full repository download), we must NOT send
        # the path parameter at all - not even as "path=None" or "path="
        # The API expects the parameter to be completely omitted
        if path:
            params["path"] = path

        try:
            response = self.client.get(
                f"/cli/repositories/{repository_id}/download", params=params
            )
            response.raise_for_status()
            data = response.json()

            # Check if this is a folder download (new API structure)
            if (
                data.get("success")
                and "files" in data
                and data.get("downloadUrl") is None
            ):
                # Folder download: return full response with files array
                return data
            # Check if this is a single file download
            elif data.get("success") and "downloadUrl" in data and data["downloadUrl"]:
                # Single file: return simplified dict
                return {
                    "url": data["downloadUrl"],
                    "sha256": data.get("sha256"),
                    "md5": data.get("md5"),
                    "path": data.get("path"),
                }
            else:
                # Fallback for old response format - return just URL
                return data.get("downloadUrl")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid or expired API token") from e
            elif e.response.status_code == 404:
                raise ApiError("Repository or path not found") from e
            raise ApiError(f"Failed to get download URL: {e}") from e

    def _stream_download(
        self,
        client: httpx.Client,
        url: str,
        output_path: Path,
        show_progress: bool,
        description: str,
    ) -> None:
        """Helper to stream download with progress tracking."""
        with client.stream("GET", url) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("Content-Length", 0))

            with open(output_path, "wb") as f:
                if show_progress and total_size > 0:
                    with tqdm(
                        total=total_size, unit="B", unit_scale=True, desc=description
                    ) as pbar:
                        for chunk in response.iter_bytes(
                            chunk_size=self.config.chunk_size
                        ):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                        f.flush()
                else:
                    for chunk in response.iter_bytes(chunk_size=self.config.chunk_size):
                        if chunk:
                            f.write(chunk)
                    f.flush()

    def download_file(
        self,
        repository_id: int,
        path: str | None = None,
        output_dir: Path | None = None,
        show_progress: bool = True,
        is_directory: bool = False,
    ) -> Path:
        """Download a file or folder from repository."""
        download_info = self.get_download_url(repository_id, path)

        # Convert string to Path if necessary
        if output_dir is not None and not isinstance(output_dir, Path):
            output_dir = Path(output_dir)

        output_dir = output_dir or self.config.download_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Check if this is a folder download (new API structure with files array)
        if isinstance(download_info, dict) and "files" in download_info:
            # Folder download: download each file individually
            if download_info.get("path"):
                # Specific folder download - create folder in output_dir
                folder_name = Path(download_info["path"]).name.rstrip("/")
                folder_path = output_dir / folder_name
                folder_path.mkdir(parents=True, exist_ok=True)
            else:
                # Full repository download - extract directly to output_dir
                folder_path = output_dir

            files = download_info["files"]
            with httpx.Client(
                timeout=httpx.Timeout(600.0, connect=30.0)
            ) as clean_client:
                for i, file_info in enumerate(files, 1):
                    file_path_str = file_info["path"]
                    file_name = file_info["name"]
                    download_url = file_info["downloadUrl"]

                    # Extract relative path
                    # For full repository download (path=null): use full path as-is
                    # For specific folder download (path="folder/"): remove folder prefix
                    if download_info.get("path"):
                        # Specific folder download - remove folder prefix
                        folder_prefix = download_info["path"]
                        if file_path_str.startswith(folder_prefix):
                            relative_path = file_path_str[len(folder_prefix) :]
                        else:
                            # Fallback to filename if path doesn't start with folder prefix
                            relative_path = file_name
                    else:
                        # Full repository download - preserve full folder structure
                        relative_path = file_path_str

                    # Create full local path with folder structure
                    local_file_path = folder_path / relative_path
                    local_file_path.parent.mkdir(parents=True, exist_ok=True)

                    # Download file
                    desc = (
                        f"{file_name} ({i}/{len(files)})"
                        if show_progress
                        else file_name
                    )
                    self._stream_download(
                        clean_client, download_url, local_file_path, show_progress, desc
                    )

            return folder_path

        # Handle single file download (dict or string)
        if isinstance(download_info, dict):
            download_url = download_info.get("url")
            file_hash = download_info.get("sha256")
        else:
            download_url = download_info
            file_hash = None

        # Determine if this is a ZIP download
        # Note: path=None (full repository) now uses files array API, not ZIP
        is_zip = download_url.endswith(".zip") or is_directory

        if is_zip:
            temp_dir = tempfile.gettempdir()
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".zip", delete=False, dir=temp_dir
            )
            download_path = Path(temp_file.name)
            temp_file.close()
        else:
            if path:
                filename = Path(path).name
            else:
                filename = f"repository_{repository_id}"
            download_path = output_dir / filename

        try:
            # Determine description for progress bar
            desc = (
                "Downloading ZIP" if is_zip else Path(path).name if path else "Download"
            )

            # Use appropriate client based on URL type
            if "X-Amz-Algorithm" in download_url:
                # Clean client for presigned URLs
                with httpx.Client(
                    timeout=httpx.Timeout(600.0, connect=30.0)
                ) as clean_client:
                    self._stream_download(
                        clean_client, download_url, download_path, show_progress, desc
                    )
            else:
                # Authenticated client for regular API URLs
                self._stream_download(
                    self.client, download_url, download_path, show_progress, desc
                )

            # Check if downloaded file is actually a ZIP (even if not expected)
            # This handles cases where API returns ZIP for single files
            if not is_zip and download_path.exists():
                # Check magic bytes for ZIP signature
                with open(download_path, "rb") as f:
                    header = f.read(4)
                    if header == b"PK\x03\x04":
                        is_zip = True
                        # Move to temp location for extraction
                        temp_dir = tempfile.gettempdir()
                        temp_zip = Path(temp_dir) / f"{download_path.stem}_detected.zip"
                        download_path.rename(temp_zip)
                        download_path = temp_zip

            # If it's a ZIP file (directory download or detected), extract it
            if is_zip:
                should_cleanup_zip = False  # Track whether to cleanup temp ZIP file
                result = download_path  # Default to downloaded file if extraction fails

                try:
                    # Security: Validate ZIP file
                    validator = ZipSecurityValidator()
                    validator.validate(download_path)

                    # Extract ZIP file
                    extractor = ZipExtractor(filter_checksums=True)
                    result, extracted_files = extractor.extract(
                        download_path, output_dir, path
                    )

                    # Extraction successful, cleanup temp ZIP
                    should_cleanup_zip = True

                except zipfile.BadZipFile as e:
                    # If ZIP is corrupted, return the downloaded file as-is (don't cleanup)
                    logger.warning(
                        f"Downloaded ZIP file is corrupted and cannot be extracted: {download_path}. "
                        f"Returning corrupted file for manual inspection. Error: {e}"
                    )
                    result = download_path
                    should_cleanup_zip = False
                finally:
                    # Clean up the temporary ZIP file only if extraction succeeded
                    if should_cleanup_zip:
                        try:
                            if download_path and download_path.exists():
                                # Try to close any open file handles first
                                import gc

                                gc.collect()

                                # Now delete the file
                                download_path.unlink()

                                # Verify it's actually deleted
                                if download_path.exists():
                                    # If still exists, try with force
                                    import os

                                    os.remove(str(download_path))
                        except Exception as e:
                            # Log the error but don't fail
                            print(
                                f"Warning: Could not delete temporary ZIP file {download_path}: {e}"
                            )

                return result
            else:
                return download_path

        except Exception as e:
            # Clean up temp file on error
            if is_zip and download_path.exists():
                try:
                    download_path.unlink()
                except Exception:
                    pass  # Ignore cleanup errors
            raise DownloadError(f"Failed to download file: {e}") from e

    def get_batch_download_info(
        self, repository_id: int, paths: list[str]
    ) -> list[FileDownloadInfo]:
        """Get download information for multiple files."""
        try:
            response = self.client.post(
                f"/cli/repositories/{repository_id}/download-list",
                json={"paths": paths},
            )
            response.raise_for_status()
            data = response.json()

            return [FileDownloadInfo(**item) for item in data.get("items", [])]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid or expired API token") from e
            raise ApiError(f"Failed to get batch download info: {e}") from e

    async def download_batch(
        self,
        repository_id: int,
        paths: list[str],
        output_dir: Path | None = None,
        raise_on_failure: bool = True,
    ) -> list[Path] | BatchDownloadResult:
        """Download multiple files in batch.

        Args:
            repository_id: Repository ID to download from
            paths: List of file paths to download
            output_dir: Directory to save downloaded files (uses config.download_dir if not specified)
            raise_on_failure: If True (default), raise BatchDownloadError on any failure.
                            If False, return BatchDownloadResult with partial success.

        Returns:
            - If raise_on_failure=True (default): list[Path] on complete success
            - If raise_on_failure=False: BatchDownloadResult with success/failure details

        Raises:
            BatchDownloadError: When raise_on_failure=True and any downloads fail.
                                Contains both successful and failed download information.

        Examples:
            Basic usage (all succeed or exception):
            >>> try:
            ...     files = await client.download_batch(123, ["/data/file1.csv"])
            ...     for file in files:  # list[Path]
            ...         process(file)
            ... except BatchDownloadError as e:
            ...     print(f"Failed: {e.failure_count}/{e.total_count}")
            ...     for failure in e.failed:
            ...         print(f"  {failure.name}: {failure.error}")
            ...     # Still process successful downloads
            ...     for file in e.successful:
            ...         process(file)

            Partial failure allowed:
            >>> result = await client.download_batch(123, paths, raise_on_failure=False)
            >>> if result.has_failures:
            ...     for failure in result.failed:
            ...         retry(failure)
        """
        download_infos = self.get_batch_download_info(repository_id, paths)
        output_dir = output_dir or self.config.download_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient() as client:
            tasks = []
            file_infos = []
            for info in download_infos:
                if info.type == "file":
                    task = self._async_download_file(
                        client,
                        info.presigned_url,
                        output_dir / info.name,
                    )
                    tasks.append(task)
                    file_infos.append(info)

            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Separate successful and failed downloads
        successful_paths: list[Path] = []
        failed_downloads: list[FailedDownload] = []

        for i, result in enumerate(results):
            if isinstance(result, Path):
                successful_paths.append(result)
            else:
                # result is an exception
                error_msg = str(result)
                failed_downloads.append(
                    FailedDownload(
                        path=file_infos[i].path,
                        name=file_infos[i].name,
                        error=error_msg,
                    )
                )

        # Handle failures based on raise_on_failure parameter
        if failed_downloads:
            if raise_on_failure:
                raise BatchDownloadError(successful_paths, failed_downloads)
            else:
                return BatchDownloadResult(
                    successful=successful_paths, failed=failed_downloads
                )

        # All successful - return simple list
        return successful_paths

    async def _async_download_file(
        self,
        client: httpx.AsyncClient,
        url: str,
        output_path: Path,
    ) -> Path:
        """Async helper for downloading a single file."""
        try:
            response = await client.get(url)
            response.raise_for_status()
            output_path.write_bytes(response.content)
            return output_path
        except Exception as e:
            raise DownloadError(f"Failed to download {output_path.name}: {e}") from e

    def upload_file(
        self,
        repository_id: int,
        file_path: Path,
        remote_path: str = "",
        show_progress: bool = True,
    ) -> dict:
        """Upload a file to dataset (repository).

        Note: httpx uses standard multipart form data upload which is efficient
        and memory-safe for files of all sizes. Progress tracking is limited to
        start/end notifications due to httpx's architecture.
        """
        # Convert to Path if string
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise UploadError(f"File not found: {file_path}")

        try:
            file_size = file_path.stat().st_size

            if show_progress:
                logger.info(
                    f"Uploading {file_path.name} ({file_size / 1024 / 1024:.2f} MB)..."
                )

            # Calculate MD5 hash for integrity verification
            md5_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    md5_hash.update(chunk)
            md5_digest = md5_hash.hexdigest()

            if show_progress:
                logger.info(f"MD5: {md5_digest}")

            # Upload file with MD5 hash
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f)}
                data = {"path": remote_path, "md5": md5_digest}
                response = self.client.post(
                    f"/cli/repositories/{repository_id}/upload", files=files, data=data
                )

            response.raise_for_status()

            if show_progress:
                logger.info(f"✓ Upload completed: {file_path.name}")

            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid or expired API token") from e
            raise UploadError(f"Failed to upload file: {e}") from e
