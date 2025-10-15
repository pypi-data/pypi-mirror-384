# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

import tempfile
import shutil
import logging
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from PySide6.QtCore import QThread, Signal
from .archive_extractor import ArchiveExtractor, ArchiveExtractionError

# Configure logging
logger = logging.getLogger(__name__)


class ModDownloadError(Exception):
    """Exception raised when mod download fails."""

    pass


class ModDownloader(QThread):
    """Handles downloading and extracting mods from GameBanana."""

    # Signals
    progress_updated = Signal(int, int)  # (bytes_downloaded, total_bytes)
    download_complete = Signal(str)  # (mod_name)
    download_failed = Signal(str)  # (error_message)

    def __init__(self, gamebanana_url: str, inactive_mods_dir: Path):
        super().__init__()
        self.gamebanana_url = gamebanana_url
        self.inactive_mods_dir = inactive_mods_dir
        self._cancelled = False
        self.expected_extension = None  # Will be set if we can extract from URL

    @staticmethod
    def parse_gamebanana_url(gamebanana_url: str) -> tuple[str, str | None]:
        """
        Parse a GameBanana URL and convert it to a direct download URL.
        Supports both direct GameBanana URLs and crosspatch MIME links.

        Args:
            gamebanana_url: URL in one of these formats:
                - "gamebanana.com/dl/{file_id}"
                - "https://gamebanana.com/dl/{file_id}"
                - "crosspatch:https://gamebanana.com/mmdl/{file_id},{type},{mod_id},{extension}"

        Returns:
            Tuple of (download_url, file_extension)
            - download_url: Direct download URL in format "https://gamebanana.com/dl/{file_id}"
            - file_extension: File extension (e.g., ".zip", ".rar") or None if unknown

        Raises:
            ModDownloadError: If URL format is invalid
        """
        url = gamebanana_url.strip()

        # Check if this is a crosspatch MIME link
        if url.startswith("crosspatch:"):
            # Remove the crosspatch: prefix
            url_part = url[len("crosspatch:") :]

            # Extract file_id and extension from the mmdl URL
            # Format: https://gamebanana.com/mmdl/{file_id},{type},{mod_id},{extension}
            try:
                # Split by comma to get all parts
                parts = url_part.split(",")

                if len(parts) < 4:
                    raise ModDownloadError(f"Invalid crosspatch format: expected 4 parts, got {len(parts)}")

                first_part = parts[0]  # URL with file_id
                extension = parts[3].strip()  # File extension

                # Validate it contains mmdl
                if "/mmdl/" not in first_part:
                    raise ModDownloadError("Crosspatch URL must contain '/mmdl/'")

                # Extract file_id from the end of the URL
                file_id = first_part.split("/mmdl/")[-1].strip()

                if not file_id:
                    raise ModDownloadError(
                        "Could not extract file ID from crosspatch URL"
                    )

                # Add dot to extension if not present
                if extension and not extension.startswith("."):
                    extension = f".{extension}"

                print(f"[ModDownloader] Extracted extension from crosspatch URL: {extension}")
                logger.info(f"Extracted extension from crosspatch URL: {extension}")

                # Construct the download URL
                return f"https://gamebanana.com/dl/{file_id}", extension
            except (IndexError, ValueError) as e:
                raise ModDownloadError(f"Invalid crosspatch URL format: {e}")

        # Handle standard GameBanana dl/ URLs
        # Add https:// if not present
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        # Validate it's a GameBanana URL
        if "gamebanana.com/dl/" not in url:
            raise ModDownloadError(
                "URL must be in format: gamebanana.com/dl/{file_id} "
                "or crosspatch:https://gamebanana.com/mmdl/{file_id},..."
            )

        # Extract the file ID to validate format
        try:
            parts = url.split("/dl/")
            if len(parts) != 2:
                raise ModDownloadError("Invalid URL format")

            file_id = parts[1].strip()
            if not file_id:
                raise ModDownloadError("File ID is missing")

            # Reconstruct clean URL (no extension info available for direct URLs)
            return f"https://gamebanana.com/dl/{file_id}", None
        except (IndexError, ValueError):
            raise ModDownloadError("Could not extract file ID from URL")

    def cancel(self) -> None:
        """Cancel the download operation."""
        self._cancelled = True

    def run(self) -> None:
        """Execute the download and extraction process."""
        temp_file = None
        temp_dir = None

        try:
            # Parse the URL and extract extension if available
            download_url, url_extension = self.parse_gamebanana_url(self.gamebanana_url)
            print(f"[ModDownloader] Downloading from URL: {download_url}")
            logger.info(f"Downloading from URL: {download_url}")

            # Download the file with progress tracking
            request = Request(
                download_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )

            with urlopen(request, timeout=30) as response:
                # Try to determine file extension from multiple sources (in priority order)
                file_extension = None

                # 1. Use extension from crosspatch URL if available
                if url_extension:
                    file_extension = url_extension
                    print(f"[ModDownloader] Using extension from URL: {file_extension}")
                    logger.info(f"Using extension from URL: {file_extension}")

                # 2. Try to get from Content-Disposition header
                if not file_extension:
                    content_disposition = response.headers.get("Content-Disposition", "")
                    if "filename=" in content_disposition:
                        # Extract filename from Content-Disposition
                        filename = content_disposition.split("filename=")[-1].strip('"')
                        file_extension = Path(filename).suffix
                        if file_extension:
                            print(f"[ModDownloader] Detected extension from Content-Disposition: {file_extension}")
                            logger.info(f"Detected extension from Content-Disposition: {file_extension}")

                # 3. Fallback to .zip if we still can't determine extension
                if not file_extension:
                    file_extension = ".zip"
                    print(f"[ModDownloader] No extension detected, defaulting to: {file_extension}")
                    logger.warning(f"No extension detected, defaulting to: {file_extension}")

                # Create a temporary file for the download with appropriate extension
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix=file_extension
                )
                temp_file_path = Path(temp_file.name)
                temp_file.close()
                print(f"[ModDownloader] Temporary file path: {temp_file_path}")
                logger.info(f"Temporary file path: {temp_file_path}")
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 8192

                with open(temp_file_path, "wb") as f:
                    while True:
                        if self._cancelled:
                            temp_file_path.unlink(missing_ok=True)
                            return

                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress_updated.emit(downloaded, total_size)

            if self._cancelled:
                temp_file_path.unlink(missing_ok=True)
                return

            # Extract the archive file
            temp_dir = Path(tempfile.mkdtemp())
            print(f"[ModDownloader] Extracting archive to: {temp_dir}")
            logger.info(f"Extracting archive to: {temp_dir}")

            ArchiveExtractor.extract(temp_file_path, temp_dir)

            if self._cancelled:
                temp_file_path.unlink(missing_ok=True)
                shutil.rmtree(temp_dir, ignore_errors=True)
                return

            # Find the mod directory in the extracted files
            # Typically, the zip contains a single directory with the mod name
            extracted_items = list(temp_dir.iterdir())

            if len(extracted_items) == 0:
                raise ModDownloadError("Extracted archive is empty")

            # If there's a single directory, use it as the mod
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                mod_source = extracted_items[0]
                mod_name = mod_source.name
            else:
                # If there are multiple items or files, use the temp dir itself
                mod_source = temp_dir
                # Try to derive mod name from the zip filename
                mod_name = temp_file_path.stem

            # Move to inactive mods directory
            self.inactive_mods_dir.mkdir(parents=True, exist_ok=True)
            destination = self.inactive_mods_dir / mod_name

            # Handle name conflicts
            counter = 1
            original_name = mod_name
            while destination.exists():
                mod_name = f"{original_name}_{counter}"
                destination = self.inactive_mods_dir / mod_name
                counter += 1

            # Move the mod to the inactive directory
            shutil.move(str(mod_source), str(destination))

            # Clean up
            temp_file_path.unlink(missing_ok=True)
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

            if not self._cancelled:
                self.download_complete.emit(mod_name)

        except (URLError, HTTPError) as e:
            error_msg = f"Network error: {e}"
            print(f"[ModDownloader] ERROR: {error_msg}")
            logger.error(error_msg, exc_info=True)
            if temp_file and Path(temp_file.name).exists():
                Path(temp_file.name).unlink(missing_ok=True)
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            if not self._cancelled:
                self.download_failed.emit(error_msg)

        except ArchiveExtractionError as e:
            error_msg = f"Archive extraction failed: {e}"
            print(f"[ModDownloader] ERROR: {error_msg}")
            logger.error(error_msg, exc_info=True)
            if temp_file and Path(temp_file.name).exists():
                Path(temp_file.name).unlink(missing_ok=True)
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            if not self._cancelled:
                self.download_failed.emit(error_msg)

        except ModDownloadError as e:
            error_msg = str(e)
            print(f"[ModDownloader] ERROR: {error_msg}")
            logger.error(error_msg, exc_info=True)
            if temp_file and Path(temp_file.name).exists():
                Path(temp_file.name).unlink(missing_ok=True)
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            if not self._cancelled:
                self.download_failed.emit(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(f"[ModDownloader] ERROR: {error_msg}")
            logger.error(error_msg, exc_info=True)
            if temp_file and Path(temp_file.name).exists():
                Path(temp_file.name).unlink(missing_ok=True)
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            if not self._cancelled:
                self.download_failed.emit(error_msg)
