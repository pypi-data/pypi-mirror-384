# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

import zipfile
import logging
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

ArchiveType = Literal["zip", "7z", "rar"]


class ArchiveExtractionError(Exception):
    """Exception raised when archive extraction fails."""

    pass


class ArchiveExtractor:
    """Handles extraction of various archive formats (zip, 7z, rar)."""

    @staticmethod
    def detect_archive_type(file_path: Path) -> ArchiveType | None:
        """
        Detect the archive type based on file extension.

        Args:
            file_path: Path to the archive file

        Returns:
            Archive type ('zip', '7z', 'rar') or None if unknown
        """
        suffix = file_path.suffix.lower()

        if suffix == ".zip":
            return "zip"
        elif suffix in [".7z", ".7zip"]:
            return "7z"
        elif suffix == ".rar":
            return "rar"

        return None

    @staticmethod
    def extract(archive_path: Path, destination: Path) -> None:
        """
        Extract an archive to the specified destination.
        Automatically detects archive type and uses appropriate extractor.

        Args:
            archive_path: Path to the archive file
            destination: Directory to extract contents to

        Raises:
            ArchiveExtractionError: If extraction fails or format is unsupported
        """
        archive_type = ArchiveExtractor.detect_archive_type(archive_path)

        if archive_type is None:
            error_msg = (
                f"Unsupported archive format: {archive_path.suffix}. "
                "Supported formats: .zip, .7z, .rar"
            )
            print(f"[ArchiveExtractor] ERROR: {error_msg}")
            logger.error(error_msg)
            raise ArchiveExtractionError(error_msg)

        print(f"[ArchiveExtractor] Detected archive type: {archive_type}")
        logger.info(f"Detected archive type: {archive_type} for file: {archive_path}")

        try:
            if archive_type == "zip":
                ArchiveExtractor._extract_zip(archive_path, destination)
            elif archive_type == "7z":
                ArchiveExtractor._extract_7z(archive_path, destination)
            elif archive_type == "rar":
                ArchiveExtractor._extract_rar(archive_path, destination)
        except Exception as e:
            error_msg = f"Failed to extract {archive_type} archive: {e}"
            print(f"[ArchiveExtractor] ERROR: {error_msg}")
            logger.error(error_msg, exc_info=True)
            raise ArchiveExtractionError(error_msg)

        print(f"[ArchiveExtractor] Successfully extracted to: {destination}")
        logger.info(f"Successfully extracted archive to: {destination}")

    @staticmethod
    def _extract_zip(archive_path: Path, destination: Path) -> None:
        """Extract a zip archive."""
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(destination)

    @staticmethod
    def _extract_7z(archive_path: Path, destination: Path) -> None:
        """Extract a 7z archive."""
        try:
            import py7zr
        except ImportError:
            raise ArchiveExtractionError(
                "py7zr library not installed. Install it with: pip install py7zr"
            )

        with py7zr.SevenZipFile(archive_path, mode="r") as archive:
            archive.extractall(destination)

    @staticmethod
    def _extract_rar(archive_path: Path, destination: Path) -> None:
        """Extract a rar archive."""
        try:
            import rarfile
        except ImportError:
            raise ArchiveExtractionError(
                "rarfile library not installed. Install it with: pip install rarfile"
            )

        with rarfile.RarFile(archive_path, "r") as rar_ref:
            rar_ref.extractall(destination)
