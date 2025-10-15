# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

import webbrowser
from typing import Callable
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QProgressBar,
    QMessageBox,
    QLabel,
    QGroupBox,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from ..services import ModDownloader, ModDownloadError
from ..models import AppConfig


class DownloadTab(QWidget):
    """Tab for downloading mods from GameBanana."""

    def __init__(
        self, config: AppConfig, on_download_complete: Callable[[], None], parent=None
    ):
        super().__init__(parent)
        self.config = config
        self.on_download_complete = on_download_complete
        self.downloader = None
        self.is_downloading = False
        self.main_window = None  # Will be set by MainWindow

        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Container widget for scroll area
        container = QWidget()
        scroll.setWidget(container)

        # Main layout inside scroll area
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        container.setLayout(layout)

        # Set scroll area as the main widget
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        main_layout.addWidget(scroll)

        # Info box group
        info_group = QGroupBox("Download Information")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        info_group.setLayout(info_layout)

        # Profile info
        self.profile_info = QLabel()
        self.profile_info.setStyleSheet("""
            QLabel {
                background-color: #e8f4f8;
                border-left: 4px solid #3498db;
                padding: 10px;
                font-weight: normal;
                border-radius: 3px;
            }
        """)
        self.update_profile_info()
        info_layout.addWidget(self.profile_info)

        # Instructions
        instructions_title = QLabel("Supported URL Formats:")
        instructions_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        info_layout.addWidget(instructions_title)

        instructions = QLabel(
            "• Direct download: <code>gamebanana.com/dl/1535503</code><br>"
            "• Crosspatch link: <code>crosspatch:https://gamebanana.com/mmdl/1535503,Mod,622573,rar</code>"
        )
        instructions.setWordWrap(True)
        instructions.setTextFormat(Qt.TextFormat.RichText)
        instructions.setStyleSheet("""
            QLabel {
                padding: 5px 10px;
                font-weight: normal;
                line-height: 1.5;
            }
        """)
        info_layout.addWidget(instructions)

        # GameBanana button
        gamebanana_btn = QPushButton("Download mods from GameBanana")
        gamebanana_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        gamebanana_btn.clicked.connect(
            lambda: webbrowser.open("https://gamebanana.com/games/21640")
        )
        info_layout.addWidget(gamebanana_btn)

        layout.addWidget(info_group)

        # URL text box
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("Paste GameBanana URL here...")
        self.url_input.setMaximumHeight(100)
        layout.addWidget(self.url_input)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Ready")
        layout.addWidget(self.progress_bar)

        # Download button
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.on_download_clicked)
        layout.addWidget(self.download_btn)

        # Horizontal separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("QFrame { color: #bdc3c7; margin: 10px 0; }")
        layout.addWidget(separator)

        # Suggested mods section
        self.suggested_group = QGroupBox("Suggested Mods")
        self.suggested_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        suggested_layout = QVBoxLayout()
        suggested_layout.setSpacing(8)
        self.suggested_group.setLayout(suggested_layout)

        # Add suggested mods
        suggested_mods = [
            ("Cyberized AI Racer Voice Pack", "https://gamebanana.com/sounds/82828"),
            ("Super Shield Transformation Mod", "https://gamebanana.com/mods/626859"),
            ("CrossTalk Renders Mod", "https://gamebanana.com/mods/622573"),
            ("Actual Button Prompts", "https://gamebanana.com/mods/622888"),
        ]

        for mod_name, mod_url in suggested_mods:
            mod_widget = self._create_mod_link_widget(mod_name, mod_url)
            suggested_layout.addWidget(mod_widget)

        # Disclaimer text
        disclaimer = QLabel("Not affiliated with mods and mod creators.")
        disclaimer.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 10px;
                font-style: italic;
                padding: 5px 10px 0px 10px;
            }
        """)
        disclaimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        suggested_layout.addWidget(disclaimer)

        layout.addWidget(self.suggested_group)

        # Set initial visibility based on config
        self.update_suggested_mods_visibility()

        layout.addStretch()

    def set_url(self, url: str) -> None:
        """
        Programmatically set the URL in the input field.
        Used when the application is launched with a crosspatch URL.
        """
        self.url_input.setPlainText(url)

    def update_profile_info(self) -> None:
        """Update the profile information display."""
        profile_name = self.config.current_profile
        self.profile_info.setText(
            f"<b>Download Target:</b> Mods will be downloaded to the <b>'{profile_name}'</b> profile"
        )

    def update_suggested_mods_visibility(self) -> None:
        """Update the visibility of the suggested mods section based on config."""
        self.suggested_group.setVisible(self.config.show_suggested_mods)

    def _create_mod_link_widget(self, mod_name: str, mod_url: str) -> QWidget:
        """Create a styled widget for a suggested mod link."""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 8px;
            }
            QFrame:hover {
                background-color: #e9ecef;
                border-color: #3498db;
            }
        """)
        container.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        container.setLayout(layout)

        # Mod name label
        name_label = QLabel(f"<b>{mod_name}</b>")
        name_label.setStyleSheet("QLabel { background: transparent; border: none; }")
        layout.addWidget(name_label)

        layout.addStretch()

        # Visit link button
        visit_btn = QPushButton("Visit Page")
        visit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        visit_btn.clicked.connect(lambda: webbrowser.open(mod_url))
        layout.addWidget(visit_btn)

        # Make entire container clickable
        container.mousePressEvent = lambda event: webbrowser.open(mod_url)

        return container

    def on_download_clicked(self) -> None:
        """Handle download/cancel button click."""
        if self.is_downloading:
            # Cancel the download
            self.cancel_download()
        else:
            # Start the download
            self.start_download()

    def start_download(self) -> None:
        """Start downloading the mod."""
        url = self.url_input.toPlainText().strip()

        if not url:
            QMessageBox.warning(self, "No URL", "Please paste a GameBanana URL.")
            return

        # Validate URL format
        try:
            # parse_gamebanana_url returns (url, extension) but we just need validation here
            _ = ModDownloader.parse_gamebanana_url(url)
        except ModDownloadError as e:
            QMessageBox.critical(
                self,
                "Invalid URL",
                f"Invalid URL format:\n\n{e}\n\n"
                "Please use one of these formats:\n"
                "• gamebanana.com/dl/1535503\n"
                "• crosspatch:https://gamebanana.com/mmdl/1535503,Mod,622573,rar",
            )
            return

        # Create and configure downloader
        self.downloader = ModDownloader(url, self.config.inactive_mods_directory)
        self.downloader.progress_updated.connect(self.on_progress_updated)
        self.downloader.download_complete.connect(self.on_download_complete_handler)
        self.downloader.download_failed.connect(self.on_download_failed)

        # Update UI state
        self.is_downloading = True
        self.download_btn.setText("Cancel")
        self.url_input.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Starting download...")

        # Disable tab switching
        if self.main_window:
            self.main_window.set_tabs_enabled(False)

        # Start download
        self.downloader.start()

    def cancel_download(self) -> None:
        """Cancel the ongoing download."""
        if self.downloader:
            self.downloader.cancel()
            self.downloader.wait()  # Wait for thread to finish

        self.reset_ui()

    def on_progress_updated(self, downloaded: int, total: int) -> None:
        """Update progress bar based on download progress."""
        if total > 0:
            percentage = int((downloaded / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(
                f"{downloaded // 1024} KB / {total // 1024} KB ({percentage}%)"
            )
        else:
            self.progress_bar.setFormat(f"{downloaded // 1024} KB downloaded...")

    def on_download_complete_handler(self, mod_name: str) -> None:
        """Handle successful download completion."""
        self.reset_ui()
        QMessageBox.information(
            self,
            "Download Complete",
            f"Mod '{mod_name}' has been downloaded and extracted successfully!",
        )
        # Trigger callback to refresh mods list
        self.on_download_complete()

    def on_download_failed(self, error_message: str) -> None:
        """Handle download failure."""
        self.reset_ui()
        QMessageBox.critical(
            self, "Download Failed", f"Failed to download mod:\n\n{error_message}"
        )

    def reset_ui(self) -> None:
        """Reset UI to initial state."""
        self.is_downloading = False
        self.download_btn.setText("Download")
        self.url_input.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Ready")

        # Re-enable tab switching
        if self.main_window:
            self.main_window.set_tabs_enabled(True)

        # Clean up downloader
        if self.downloader:
            self.downloader.deleteLater()
            self.downloader = None
