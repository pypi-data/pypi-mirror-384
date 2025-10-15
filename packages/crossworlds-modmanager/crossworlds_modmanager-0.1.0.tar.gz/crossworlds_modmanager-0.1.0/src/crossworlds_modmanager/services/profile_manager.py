# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

import shutil
from pathlib import Path
from ..models import AppConfig, Profile


class ProfileManager:
    """Business logic for managing mod profiles."""

    DEFAULT_PROFILE = "Default"

    def __init__(self, config: AppConfig):
        self.config = config
        # Ensure Default profile exists
        self.ensure_default_profile()

    @property
    def profiles_base_directory(self) -> Path:
        """Return the base directory where profiles are stored."""
        return self.config.base_game_directory / "mods"

    def ensure_default_profile(self) -> None:
        """Ensure the Default profile directory and config entry exist."""
        default_profile_path = self.profiles_base_directory / self.DEFAULT_PROFILE
        default_profile_path.mkdir(parents=True, exist_ok=True)

        # Ensure Default profile exists in config
        if self.DEFAULT_PROFILE not in self.config.profiles:
            self.config.profiles[self.DEFAULT_PROFILE] = Profile()

    def get_available_profiles(self) -> list[str]:
        """
        Get list of available profile names (subdirectories in mods folder).

        Returns:
            List of profile names (always includes "Default")
        """
        # Ensure Default profile exists
        self.ensure_default_profile()

        profiles_dir = self.profiles_base_directory
        if not profiles_dir.exists():
            return [self.DEFAULT_PROFILE]

        profiles = []
        for item in profiles_dir.iterdir():
            if item.is_dir():
                profiles.append(item.name)

        return sorted(profiles)

    def create_profile(self, profile_name: str) -> bool:
        """
        Create a new profile directory and config entry.

        Args:
            profile_name: Name of the profile to create

        Returns:
            True if created successfully, False if already exists
        """
        profile_path = self.profiles_base_directory / profile_name
        if profile_path.exists():
            return False

        profile_path.mkdir(parents=True, exist_ok=True)

        # Create config entry for new profile
        if profile_name not in self.config.profiles:
            self.config.profiles[profile_name] = Profile()

        return True

    def rename_profile(self, old_name: str, new_name: str) -> bool:
        """
        Rename an existing profile.

        Args:
            old_name: Current profile name
            new_name: New profile name

        Returns:
            True if renamed successfully, False otherwise
        """
        old_path = self.profiles_base_directory / old_name
        new_path = self.profiles_base_directory / new_name

        if not old_path.exists() or new_path.exists():
            return False

        old_path.rename(new_path)

        # Update config entries
        if old_name in self.config.profiles:
            self.config.profiles[new_name] = self.config.profiles.pop(old_name)

        # Update current_profile in config if it was renamed
        if self.config.current_profile == old_name:
            self.config.current_profile = new_name

        return True

    def delete_profile(self, profile_name: str) -> bool:
        """
        Delete a profile directory and config entry.

        Args:
            profile_name: Name of the profile to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        # Cannot delete the Default profile
        if profile_name == self.DEFAULT_PROFILE:
            return False

        profile_path = self.profiles_base_directory / profile_name
        if not profile_path.exists():
            return False

        shutil.rmtree(profile_path)

        # Remove config entry
        if profile_name in self.config.profiles:
            del self.config.profiles[profile_name]

        # Switch to Default profile if the deleted profile was current
        if self.config.current_profile == profile_name:
            self.config.current_profile = self.DEFAULT_PROFILE

        return True
