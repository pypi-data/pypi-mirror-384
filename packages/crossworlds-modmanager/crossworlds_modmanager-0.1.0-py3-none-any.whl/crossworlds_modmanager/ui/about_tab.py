# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
)

from .widgets import ClickableLinkLabel
from crossworlds_modmanager.__about__ import __version__


class AboutTab(QWidget):
    """Tab displaying application information."""

    def __init__(self):
        super().__init__()

        # Main layout with margins
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        self.setLayout(main_layout)

        # Center container
        center_widget = QWidget()
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(20)
        center_widget.setLayout(center_layout)

        # Title
        title = QLabel("Crossworlds Mod Manager")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title)

        # Version
        version_label = QLabel(f"Version: {__version__}")
        version_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7f8c8d;
                padding: 5px;
            }
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(version_label)

        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        separator1.setStyleSheet("QFrame { color: #bdc3c7; }")
        center_layout.addWidget(separator1)

        # Description
        description = QLabel(
            "A powerful mod manager for Sonic Racing: CrossWorlds\n"
            "Manage, organize, and apply mods with ease"
        )
        description.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #34495e;
                padding: 10px;
                line-height: 1.6;
            }
        """)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        center_layout.addWidget(description)

        center_layout.addSpacing(10)

        # Links section
        links_widget = QWidget()
        links_layout = QVBoxLayout()
        links_layout.setSpacing(10)
        links_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        links_widget.setLayout(links_layout)

        # GitHub link
        github_label = QLabel("Repository")
        github_label.setStyleSheet("QLabel { font-size: 12px; color: #7f8c8d; font-weight: bold; }")
        github_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        links_layout.addWidget(github_label)

        github_link = ClickableLinkLabel(
            "github.com/Yiannis128/crossworlds-modmanager",
            "https://github.com/Yiannis128/crossworlds-modmanager"
        )
        github_link.setStyleSheet("""
            QLabel {
                color: #3498db;
                font-size: 13px;
                text-decoration: underline;
                padding: 5px;
            }
            QLabel:hover {
                color: #2980b9;
            }
        """)
        github_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        links_layout.addWidget(github_link)

        links_layout.addSpacing(5)

        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        separator2.setStyleSheet("QFrame { color: #bdc3c7; }")
        center_layout.addWidget(separator2)

        center_layout.addWidget(links_widget)

        # Credits section
        credits_widget = QWidget()
        credits_layout = QVBoxLayout()
        credits_layout.setSpacing(8)
        credits_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_widget.setLayout(credits_layout)

        # Developer
        dev_label = QLabel("Developer")
        dev_label.setStyleSheet("QLabel { font-size: 12px; color: #7f8c8d; font-weight: bold; }")
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_layout.addWidget(dev_label)

        dev_link = ClickableLinkLabel(
            "Yiannis Charalambous",
            "https://github.com/Yiannis128"
        )
        dev_link.setStyleSheet("""
            QLabel {
                color: #3498db;
                font-size: 13px;
                text-decoration: underline;
                padding: 5px;
            }
            QLabel:hover {
                color: #2980b9;
            }
        """)
        dev_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_layout.addWidget(dev_link)

        credits_layout.addSpacing(5)

        # Made with
        made_with = QLabel("Built with Claude Code")
        made_with.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #95a5a6;
                font-style: italic;
                padding: 5px;
            }
        """)
        made_with.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_layout.addWidget(made_with)

        center_layout.addWidget(credits_widget)

        # License
        center_layout.addSpacing(10)
        license_label = QLabel("Licensed under AGPL-3.0")
        license_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #95a5a6;
                padding: 5px;
            }
        """)
        license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(license_label)

        # Add center widget to main layout with stretch
        main_layout.addStretch()
        main_layout.addWidget(center_widget)
        main_layout.addStretch()
