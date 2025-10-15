# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

from typing import Callable
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QHBoxLayout,
    QMessageBox,
    QComboBox,
    QInputDialog,
    QGroupBox,
    QPushButton,
)

from ..models import AppConfig
from ..services import ProfileManager


class ProfilesTab(QWidget):
    """Tab for managing mod profiles."""

    def __init__(
        self,
        config: AppConfig,
        on_profile_changed: Callable[[], None] | None = None,
        on_profiles_list_changed: Callable[[], None] | None = None,
    ):
        super().__init__()
        self.config = config
        self.on_profile_changed_callback = on_profile_changed
        self.on_profiles_list_changed_callback = on_profiles_list_changed
        self.profile_manager = ProfileManager(config)

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Profile management section
        profile_group = QGroupBox("Mod Profiles")
        profile_layout = QVBoxLayout()

        # Profile selector
        profile_selector_layout = QFormLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self.on_profile_changed)
        profile_selector_layout.addRow("Current Profile:", self.profile_combo)
        profile_layout.addLayout(profile_selector_layout)

        # Profile management buttons
        profile_buttons_layout = QHBoxLayout()

        add_profile_btn = QPushButton("Add Profile")
        add_profile_btn.clicked.connect(self.add_profile)
        profile_buttons_layout.addWidget(add_profile_btn)

        rename_profile_btn = QPushButton("Rename Profile")
        rename_profile_btn.clicked.connect(self.rename_profile)
        profile_buttons_layout.addWidget(rename_profile_btn)

        delete_profile_btn = QPushButton("Delete Profile")
        delete_profile_btn.clicked.connect(self.delete_profile)
        profile_buttons_layout.addWidget(delete_profile_btn)

        profile_buttons_layout.addStretch()
        profile_layout.addLayout(profile_buttons_layout)

        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)

        layout.addStretch()

        # Load profiles
        self.refresh_profiles()

    def refresh_profiles(self) -> None:
        """Refresh the list of available profiles in the combobox."""
        # Block signals to prevent triggering on_profile_changed
        self.profile_combo.blockSignals(True)

        # Clear and repopulate
        self.profile_combo.clear()

        # Get available profiles
        profiles = self.profile_manager.get_available_profiles()
        for profile in profiles:
            self.profile_combo.addItem(profile, profile)

        # Select current profile (always has a value, defaults to "Default")
        index = self.profile_combo.findData(self.config.current_profile)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)
        else:
            # Fallback to Default if current profile not found
            index = self.profile_combo.findData("Default")
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)

        # Re-enable signals
        self.profile_combo.blockSignals(False)

    def update_current_profile_selector(self) -> None:
        """Update the profile selector to match the current config without triggering signals."""
        # Block signals to prevent triggering on_profile_changed
        self.profile_combo.blockSignals(True)

        # Select current profile
        index = self.profile_combo.findData(self.config.current_profile)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)

        # Re-enable signals
        self.profile_combo.blockSignals(False)

    def on_profile_changed(self, index: int) -> None:
        """Handle profile selection change."""
        profile_name = self.profile_combo.itemData(index)
        self.config.current_profile = profile_name

        # Save config and sync with other tabs if callback provided
        if self.on_profile_changed_callback:
            self.on_profile_changed_callback()

    def add_profile(self) -> None:
        """Add a new profile."""
        profile_name, ok = QInputDialog.getText(
            self, "Add Profile", "Enter profile name:"
        )

        if ok and profile_name:
            # Validate profile name
            if "/" in profile_name or "\\" in profile_name:
                QMessageBox.warning(
                    self,
                    "Invalid Name",
                    "Profile name cannot contain slashes.",
                )
                return

            # Create profile
            if self.profile_manager.create_profile(profile_name):
                self.refresh_profiles()
                # Notify other tabs that profile list changed
                if self.on_profiles_list_changed_callback:
                    self.on_profiles_list_changed_callback()
                # Select the new profile
                index = self.profile_combo.findData(profile_name)
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
                QMessageBox.information(
                    self,
                    "Profile Created",
                    f"Profile '{profile_name}' has been created.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Profile Exists",
                    f"Profile '{profile_name}' already exists.",
                )

    def rename_profile(self) -> None:
        """Rename the selected profile."""
        old_name = self.profile_combo.currentData()

        # Cannot rename the Default profile
        if old_name == "Default":
            QMessageBox.warning(
                self,
                "Cannot Rename Default",
                "The Default profile cannot be renamed.",
            )
            return

        new_name, ok = QInputDialog.getText(
            self,
            "Rename Profile",
            f"Rename profile '{old_name}' to:",
            text=old_name,
        )

        if ok and new_name and new_name != old_name:
            # Validate profile name
            if "/" in new_name or "\\" in new_name:
                QMessageBox.warning(
                    self,
                    "Invalid Name",
                    "Profile name cannot contain slashes.",
                )
                return

            # Rename profile
            if self.profile_manager.rename_profile(old_name, new_name):
                self.refresh_profiles()
                # Notify other tabs that profile list changed
                if self.on_profiles_list_changed_callback:
                    self.on_profiles_list_changed_callback()
                # Select the renamed profile
                index = self.profile_combo.findData(new_name)
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
                QMessageBox.information(
                    self,
                    "Profile Renamed",
                    f"Profile renamed from '{old_name}' to '{new_name}'.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Rename Failed",
                    f"Failed to rename profile. Profile '{new_name}' may already exist.",
                )

    def delete_profile(self) -> None:
        """Delete the selected profile."""
        profile_name = self.profile_combo.currentData()

        # Cannot delete the Default profile
        if profile_name == "Default":
            QMessageBox.warning(
                self,
                "Cannot Delete Default",
                "The Default profile cannot be deleted.",
            )
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete profile '{profile_name}'?\n\n"
            "This will permanently delete all mods in this profile.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            if self.profile_manager.delete_profile(profile_name):
                self.refresh_profiles()
                # Notify other tabs that profile list changed
                if self.on_profiles_list_changed_callback:
                    self.on_profiles_list_changed_callback()
                # Select Default profile
                index = self.profile_combo.findData("Default")
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
                QMessageBox.information(
                    self,
                    "Profile Deleted",
                    f"Profile '{profile_name}' has been deleted.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Deletion Failed",
                    f"Failed to delete profile '{profile_name}'.",
                )
