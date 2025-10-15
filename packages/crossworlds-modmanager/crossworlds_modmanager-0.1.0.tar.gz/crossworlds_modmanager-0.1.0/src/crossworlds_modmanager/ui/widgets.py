# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

import subprocess
import sys
import webbrowser
from pathlib import Path
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor


class ClickableDirectoryLabel(QLabel):
    """A clickable label that opens a directory in file explorer."""

    def __init__(self, text: str = ""):
        super().__init__(text)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet("color: gray; text-decoration: underline;")
        self.setWordWrap(True)

    def mousePressEvent(self, event):
        """Handle mouse click to open directory."""
        if event.button() == Qt.LeftButton:
            directory = Path(self.text())
            if directory.exists():
                self.open_directory(directory)

    def open_directory(self, path: Path) -> None:
        """Open directory in the system file explorer."""
        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", str(path)])
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)])
            else:  # Linux and other Unix-like systems
                subprocess.run(["xdg-open", str(path)])
        except Exception:
            # Silently fail if we can't open the directory
            pass


class ClickableLinkLabel(QLabel):
    """A clickable label that opens a URL in the web browser."""

    def __init__(self, text: str, url: str):
        super().__init__(text)
        self.url = url
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet("color: blue; text-decoration: underline;")

    def mousePressEvent(self, event):
        """Handle mouse click to open URL."""
        if event.button() == Qt.LeftButton:
            try:
                webbrowser.open(self.url)
            except Exception:
                pass
