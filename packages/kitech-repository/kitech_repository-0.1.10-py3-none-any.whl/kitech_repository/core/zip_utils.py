"""ZIP file security validation and extraction utilities."""

import zipfile
from pathlib import Path

from kitech_repository.core.exceptions import DownloadError


class ZipSecurityValidator:
    """Validates ZIP files for security issues (ZIP bombs, path traversal)."""

    MAX_EXTRACTION_RATIO = 100  # 100:1 compression ratio
    MAX_UNCOMPRESSED_SIZE = 10 * 1024**3  # 10GB

    def validate(self, zip_path: Path) -> None:
        """Validate ZIP file for security issues.

        Args:
            zip_path: Path to ZIP file to validate

        Raises:
            DownloadError: If ZIP file has security issues
        """
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            self._check_zip_bomb(zip_ref)

    def _check_zip_bomb(self, zip_ref: zipfile.ZipFile) -> None:
        """Check for ZIP bomb attacks.

        Args:
            zip_ref: Open ZipFile reference

        Raises:
            DownloadError: If potential ZIP bomb detected
        """
        total_compressed = sum(zinfo.compress_size for zinfo in zip_ref.infolist())
        total_uncompressed = sum(zinfo.file_size for zinfo in zip_ref.infolist())

        if total_uncompressed > self.MAX_UNCOMPRESSED_SIZE:
            raise DownloadError(
                f"ZIP file too large: {total_uncompressed / 1024**3:.2f}GB"
            )

        if (
            total_compressed > 0
            and (total_uncompressed / total_compressed) > self.MAX_EXTRACTION_RATIO
        ):
            raise DownloadError(
                f"Potential ZIP bomb detected (compression ratio: {total_uncompressed / total_compressed:.1f}:1)"
            )


class ZipExtractor:
    """Extracts ZIP files with security validation."""

    def __init__(self, filter_checksums: bool = True):
        """Initialize ZIP extractor.

        Args:
            filter_checksums: Whether to filter out .sha256 checksum files
        """
        self.filter_checksums = filter_checksums

    def extract(
        self, zip_path: Path, output_dir: Path, requested_path: str | None = None
    ) -> tuple[Path, list[str]]:
        """Extract ZIP file to output directory.

        Args:
            zip_path: Path to ZIP file
            output_dir: Directory to extract to
            requested_path: Original requested path (for determining result path)

        Returns:
            Tuple of (result_path, extracted_files)
            - result_path: Path to extracted content (file or directory)
            - extracted_files: List of extracted file paths

        Raises:
            DownloadError: If extraction fails or path traversal detected
        """
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # List all files in the ZIP
            zip_contents = zip_ref.namelist()

            # Filter out checksum files if requested
            actual_files = (
                [f for f in zip_contents if not f.endswith(".sha256")]
                if self.filter_checksums
                else zip_contents
            )

            # Check for empty ZIP (API bug: returns ZIP with only checksums for single files)
            # Allow empty ZIP for directories or full repository download
            is_directory_download = not requested_path or (requested_path and requested_path.endswith("/"))
            if not actual_files and requested_path and not is_directory_download:
                raise DownloadError(
                    f"API returned empty ZIP for single file download (path: {requested_path}). "
                    f"The ZIP only contains checksum files. This may be an API bug. "
                    f"ZIP contents: {zip_contents}"
                )

            if not actual_files:
                return output_dir, []

            # Security: Validate all paths before extraction
            self._validate_paths(actual_files, output_dir)

            # Extract files
            for file in actual_files:
                zip_ref.extract(file, output_dir)

            # Determine result path
            result = self._determine_result_path(
                actual_files, output_dir, requested_path
            )

            return result, actual_files

    def _validate_paths(self, files: list[str], output_dir: Path) -> None:
        """Validate all paths to prevent path traversal attacks.

        Args:
            files: List of file paths to validate
            output_dir: Output directory

        Raises:
            DownloadError: If path traversal attempt detected
        """
        output_dir_resolved = output_dir.resolve()
        for file in files:
            target_path = (output_dir / file).resolve()
            try:
                target_path.relative_to(output_dir_resolved)
            except ValueError:
                raise DownloadError(
                    f"Path traversal attempt detected: {file}"
                ) from None

    def _determine_result_path(
        self, extracted_files: list[str], output_dir: Path, requested_path: str | None
    ) -> Path:
        """Determine the final result path based on extracted files.

        Args:
            extracted_files: List of extracted file paths
            output_dir: Output directory
            requested_path: Original requested path

        Returns:
            Path to extracted content (file or directory)
        """
        if requested_path:
            # If path was specified, return the extracted directory
            extracted_path = output_dir / Path(requested_path).name
            if extracted_path.exists():
                return extracted_path
            return output_dir

        # Otherwise, find the top-level directory that was extracted
        top_dirs = set()
        for file in extracted_files:
            parts = Path(file).parts
            if parts:
                top_dirs.add(parts[0])

        if len(top_dirs) == 1:
            return output_dir / list(top_dirs)[0]

        return output_dir
