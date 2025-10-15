# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget
from PySide6.QtCore import Qt

from ..models import AppConfig, ConfigManager
from ..services import ModManager
from .mods_tab import ModsTab
from .profiles_tab import ProfilesTab
from .settings_tab import SettingsTab
from .download_tab import DownloadTab
from .about_tab import AboutTab


class MainWindow(QMainWindow):
    """Main application window with tabs."""

    def __init__(self, initial_download_url: str | None = None):
        super().__init__()

        # Load configuration
        self.config = ConfigManager.load()
        self.mod_manager = ModManager(self.config)

        # Set up the window
        self.setWindowTitle("Crossworlds Mod Manager")
        self.setMinimumSize(800, 600)

        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create tabs
        self.mods_tab = ModsTab(
            self.mod_manager, self.on_profile_changed, self.on_mods_applied
        )
        self.mods_tab.main_window = self  # Set reference to MainWindow
        self.profiles_tab = ProfilesTab(
            self.config, self.on_profile_changed, self.on_profiles_list_changed
        )
        self.download_tab = DownloadTab(self.config, self.on_download_complete)
        self.download_tab.main_window = self  # Set reference to MainWindow
        self.settings_tab = SettingsTab(self.config, self.on_settings_changed)
        self.settings_tab.main_window = self  # Set reference to MainWindow
        self.about_tab = AboutTab()

        # Add tabs
        self.tabs.addTab(self.mods_tab, "Mods")
        self.tabs.addTab(self.profiles_tab, "Profiles")
        self.tabs.addTab(self.download_tab, "Download")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.about_tab, "About")

        # Create status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        # Validate config and update UI
        self.validate_config()

        # Initial refresh if config is valid
        if self.config.is_valid()[0]:
            self.mods_tab.refresh()

        # If launched with a download URL, switch to Download tab and populate URL
        if initial_download_url:
            self.tabs.setCurrentWidget(self.download_tab)
            self.download_tab.set_url(initial_download_url)

    def validate_config(self) -> None:
        """Validate configuration and update UI state."""
        is_valid, error_message = self.config.is_valid()
        self.mods_tab.set_config_validity(is_valid, error_message)

    def on_settings_changed(self) -> None:
        """Handle settings changes."""
        # Save configuration
        ConfigManager.save(self.config)

        # Update mod manager with new config
        self.mod_manager.config = self.config

        # Validate config and update UI
        self.validate_config()

        # Update download tab's profile info
        self.download_tab.update_profile_info()

        # Update suggested mods visibility
        self.download_tab.update_suggested_mods_visibility()

        # Refresh mods list if config is valid
        if self.config.is_valid()[0]:
            self.mods_tab.refresh()

    def on_download_complete(self) -> None:
        """Handle download completion by refreshing mods list."""
        if self.config.is_valid()[0]:
            self.mods_tab.refresh()

    def on_profile_changed(self) -> None:
        """Handle profile changes by saving config and syncing UI."""
        # Save configuration to persist profile selection
        ConfigManager.save(self.config)

        # Update profile selectors in both tabs to stay in sync
        self.mods_tab.update_current_profile_selector()
        self.profiles_tab.update_current_profile_selector()

        # Update directory labels in settings tab to reflect new profile
        self.settings_tab.update_preview()

        # Validate config and update UI
        self.validate_config()

        # Update download tab's profile info
        self.download_tab.update_profile_info()

        # Refresh mods list if config is valid
        if self.config.is_valid()[0]:
            self.mods_tab.refresh()

    def on_mods_applied(self) -> None:
        """Handle mods being applied by saving config to persist mod order."""
        ConfigManager.save(self.config)

    def on_profiles_list_changed(self) -> None:
        """Handle profile list changes (add/rename/delete) by refreshing both tabs."""
        # Refresh profile lists in both tabs
        self.mods_tab.refresh_profiles()
        self.profiles_tab.refresh_profiles()

    def set_tabs_enabled(self, enabled: bool) -> None:
        """Enable or disable tab switching."""
        if enabled:
            # Re-enable all tabs and tab bar
            for i in range(self.tabs.count()):
                self.tabs.setTabEnabled(i, True)
            self.tabs.tabBar().setEnabled(True)
        else:
            # Disable tab switching (but keep current tab content enabled)
            # Disable all other tabs
            current_index = self.tabs.currentIndex()
            for i in range(self.tabs.count()):
                if i != current_index:
                    self.tabs.setTabEnabled(i, False)

            # Disable tab bar to prevent clicking on tabs
            self.tabs.tabBar().setEnabled(False)
