# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

import subprocess
from pathlib import Path
from typing import Callable
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QCheckBox,
    QLabel,
    QGroupBox,
)
from PySide6.QtCore import Qt

from ..models import AppConfig
from ..models.config import ConfigManager
from .widgets import ClickableDirectoryLabel


class SettingsTab(QWidget):
    """Tab for configuring application settings."""

    def __init__(
        self,
        config: AppConfig,
        on_settings_changed: Callable[[], None],
    ):
        super().__init__()
        self.config = config
        self.on_settings_changed = on_settings_changed
        self.main_window = None  # Will be set by MainWindow

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Form layout for settings
        form_layout = QFormLayout()

        # Base game directory
        game_dir_layout = QHBoxLayout()
        self.game_dir_input = QLineEdit(str(config.base_game_directory))
        game_dir_layout.addWidget(self.game_dir_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_game_directory)
        game_dir_layout.addWidget(browse_btn)

        form_layout.addRow("Base Game Directory:", game_dir_layout)

        # Relative active mods directory (editable)
        self.relative_dir_input = QLineEdit(config.relative_active_mods_dir)
        form_layout.addRow("Relative Active Mods Dir:", self.relative_dir_input)

        # Game directory (clickable, opens in file explorer)
        self.game_dir_label = ClickableDirectoryLabel(str(config.base_game_directory))
        form_layout.addRow("Game Directory:", self.game_dir_label)

        # Computed active mods directory (clickable, opens in file explorer)
        self.active_dir_label = ClickableDirectoryLabel(
            str(config.active_mods_directory)
        )
        form_layout.addRow("Active Mods Directory:", self.active_dir_label)

        # Computed inactive mods directory (clickable, opens in file explorer)
        self.inactive_dir_label = ClickableDirectoryLabel(
            str(config.inactive_mods_directory)
        )
        form_layout.addRow("Inactive Mods Directory:", self.inactive_dir_label)

        # Config file path (selectable label for copy/paste)
        self.config_file_label = QLabel(str(ConfigManager.CONFIG_FILE))
        self.config_file_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.config_file_label.setStyleSheet("color: #2980b9;")
        form_layout.addRow("Config File:", self.config_file_label)

        layout.addLayout(form_layout)

        # Show suggested mods checkbox with description
        self.show_suggested_mods_checkbox = QCheckBox("Show Suggested Mods")
        self.show_suggested_mods_checkbox.setChecked(config.show_suggested_mods)
        layout.addWidget(self.show_suggested_mods_checkbox)

        suggested_mods_description = QLabel(
            "Will show suggested mods in the Downloads tab. "
            "Note that no mods or their authors are affiliated with this mod manager."
        )
        suggested_mods_description.setWordWrap(True)
        suggested_mods_description.setStyleSheet(
            "color: #7f8c8d; font-size: 10px; margin-left: 25px; margin-bottom: 10px;"
        )
        layout.addWidget(suggested_mods_description)

        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()

        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        save_layout.addWidget(save_btn)

        layout.addLayout(save_layout)

        # MIME Handler Registration section
        mime_group = QGroupBox("MIME Handler Registration")
        mime_layout = QVBoxLayout()

        mime_description = QLabel(
            "Register this application to handle crosspatch:// URLs from your browser "
            "and add a desktop shortcut. "
            "This allows you to click mod download links in GameBanana and have them "
            "automatically open in the mod manager."
        )
        mime_description.setWordWrap(True)
        mime_description.setStyleSheet(
            "color: #7f8c8d; font-size: 10px; margin-bottom: 10px;"
        )
        mime_layout.addWidget(mime_description)

        # Buttons layout
        mime_buttons_layout = QHBoxLayout()
        mime_buttons_layout.addStretch()

        register_btn = QPushButton("Register Application")
        register_btn.clicked.connect(self.register_application)
        mime_buttons_layout.addWidget(register_btn)

        unregister_btn = QPushButton("Unregister Application")
        unregister_btn.clicked.connect(self.unregister_application)
        mime_buttons_layout.addWidget(unregister_btn)

        mime_layout.addLayout(mime_buttons_layout)
        mime_group.setLayout(mime_layout)
        layout.addWidget(mime_group)

        layout.addStretch()

        # Connect input changes to update preview
        self.game_dir_input.textChanged.connect(self.update_preview)
        self.relative_dir_input.textChanged.connect(self.update_preview)

    def browse_game_directory(self) -> None:
        """Open a directory browser for selecting the game directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Game Directory", str(self.config.base_game_directory)
        )

        if directory:
            self.game_dir_input.setText(directory)

    def update_preview(self) -> None:
        """Update the preview of all directory labels."""
        base_dir = Path(self.game_dir_input.text())
        relative_dir = self.relative_dir_input.text()
        active_dir = base_dir / relative_dir / "~mods"
        inactive_dir = base_dir / "mods" / self.config.current_profile
        self.game_dir_label.setText(str(base_dir))
        self.active_dir_label.setText(str(active_dir))
        self.inactive_dir_label.setText(str(inactive_dir))

    def save_settings(self) -> None:
        """Save the settings."""
        # Update config
        self.config.base_game_directory = Path(self.game_dir_input.text())
        self.config.relative_active_mods_dir = self.relative_dir_input.text()
        self.config.show_suggested_mods = self.show_suggested_mods_checkbox.isChecked()

        # Validate configuration
        is_valid, error_message = self.config.is_valid()

        if is_valid:
            # Trigger callback to save and update UI
            self.on_settings_changed()
            QMessageBox.information(
                self, "Settings Saved", "Settings have been saved successfully!"
            )
        else:
            # Still save but warn the user
            self.on_settings_changed()
            QMessageBox.warning(
                self,
                "Configuration Invalid",
                f"Settings saved, but configuration is invalid:\n\n{error_message}\n\n"
                "Please correct the settings to use the mod manager.",
            )

    def register_application(self) -> None:
        """Register the application as a MIME handler for crosspatch:// URLs."""
        try:
            result = subprocess.run(
                ["crossworlds-modmanager-register"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                if self.main_window:
                    self.main_window.statusBar().showMessage(
                        "Application registered successfully", 5000
                    )
                QMessageBox.information(
                    self,
                    "Registration Successful",
                    "The application has been registered as a handler for crosspatch:// URLs.\n\n"
                    "You can now click crosspatch links in your browser and they will "
                    "automatically open in the mod manager.",
                )
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                if self.main_window:
                    self.main_window.statusBar().showMessage(
                        "Registration failed", 5000
                    )
                QMessageBox.warning(
                    self,
                    "Registration Failed",
                    f"Failed to register the application:\n\n{error_msg}",
                )
        except FileNotFoundError:
            if self.main_window:
                self.main_window.statusBar().showMessage(
                    "Registration command not found", 5000
                )
            QMessageBox.warning(
                self,
                "Command Not Found",
                "The 'crossworlds-modmanager-register' command was not found.\n\n"
                "Make sure the application is properly installed.",
            )
        except subprocess.TimeoutExpired:
            if self.main_window:
                self.main_window.statusBar().showMessage(
                    "Registration command timed out", 5000
                )
            QMessageBox.warning(
                self, "Timeout", "The registration command timed out."
            )
        except Exception as e:
            if self.main_window:
                self.main_window.statusBar().showMessage(
                    f"Registration error: {str(e)}", 5000
                )
            QMessageBox.warning(
                self, "Error", f"An error occurred during registration:\n\n{str(e)}"
            )

    def unregister_application(self) -> None:
        """Unregister the application as a MIME handler for crosspatch:// URLs."""
        try:
            result = subprocess.run(
                ["crossworlds-modmanager-unregister"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                if self.main_window:
                    self.main_window.statusBar().showMessage(
                        "Application unregistered successfully", 5000
                    )
                QMessageBox.information(
                    self,
                    "Unregistration Successful",
                    "The application has been unregistered as a handler for crosspatch:// URLs.",
                )
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                if self.main_window:
                    self.main_window.statusBar().showMessage(
                        "Unregistration failed", 5000
                    )
                QMessageBox.warning(
                    self,
                    "Unregistration Failed",
                    f"Failed to unregister the application:\n\n{error_msg}",
                )
        except FileNotFoundError:
            if self.main_window:
                self.main_window.statusBar().showMessage(
                    "Unregistration command not found", 5000
                )
            QMessageBox.warning(
                self,
                "Command Not Found",
                "The 'crossworlds-modmanager-unregister' command was not found.\n\n"
                "Make sure the application is properly installed.",
            )
        except subprocess.TimeoutExpired:
            if self.main_window:
                self.main_window.statusBar().showMessage(
                    "Unregistration command timed out", 5000
                )
            QMessageBox.warning(
                self, "Timeout", "The unregistration command timed out."
            )
        except Exception as e:
            if self.main_window:
                self.main_window.statusBar().showMessage(
                    f"Unregistration error: {str(e)}", 5000
                )
            QMessageBox.warning(
                self,
                "Error",
                f"An error occurred during unregistration:\n\n{str(e)}",
            )
