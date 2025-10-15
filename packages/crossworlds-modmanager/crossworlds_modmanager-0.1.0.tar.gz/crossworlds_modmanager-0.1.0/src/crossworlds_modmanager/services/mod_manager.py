# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

import shutil
from pathlib import Path
from typing import List
from ..models import AppConfig, Mod


class ModManager:
    """Business logic for managing UE5 mods."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.mods: list[Mod] = []

    def _cleanup_active_directory(self) -> None:
        """
        Clean up the active mods directory by:
        1. Moving mod folders without valid xxx. prefix to Default profile
        2. Removing mod folders that belong to other profiles (not current)
        3. Deleting mods with valid prefix that don't exist in any profile
        """
        active_dir = self.config.active_mods_directory
        inactive_dir = self.config.inactive_mods_directory
        profiles_base_dir = self.config.base_game_directory / "mods"
        default_profile_dir = profiles_base_dir / "Default"

        # Only proceed if active directory exists
        if not active_dir.exists():
            return

        # Ensure Default profile directory exists
        default_profile_dir.mkdir(parents=True, exist_ok=True)

        # Get all available profiles
        all_profiles = []
        if profiles_base_dir.exists():
            for item in profiles_base_dir.iterdir():
                if item.is_dir():
                    all_profiles.append(item)

        # Scan for mod directories that need cleanup
        for item in active_dir.iterdir():
            # Only process directories
            if not item.is_dir():
                continue

            dirname = item.name
            # Check if dirname matches the ###. pattern
            parts = dirname.split(".", 1)

            has_valid_prefix = (
                len(parts) == 2 and len(parts[0]) == 3 and parts[0].isdigit()
            )

            if not has_valid_prefix:
                # No valid prefix - move to Default as orphan
                dest = default_profile_dir / dirname
                if not dest.exists():
                    shutil.move(str(item), str(dest))
            else:
                # Has valid prefix - check if it belongs to current profile
                from ..models import Mod
                mod_name, _ = Mod.parse_dirname(dirname)
                mod_in_current_profile = (inactive_dir / mod_name).exists()

                if not mod_in_current_profile:
                    # Not in current profile - check if it exists in ANY other profile
                    found_in_other_profile = False
                    for profile_dir in all_profiles:
                        if profile_dir == inactive_dir:
                            continue  # Skip current profile, already checked
                        if (profile_dir / mod_name).exists():
                            found_in_other_profile = True
                            break

                    # Remove from active regardless - either belongs to another profile
                    # or doesn't exist in any profile (orphaned)
                    shutil.rmtree(item)

    def refresh(self) -> list[Mod]:
        """
        Scan both active and inactive mod directories and build the mod list.
        Load mod order from the profile configuration.

        Returns:
            List of mods with their current state
        """
        # Ensure Default profile exists before any operations
        default_profile_dir = self.config.base_game_directory / "mods" / "Default"
        default_profile_dir.mkdir(parents=True, exist_ok=True)

        active_dir = self.config.active_mods_directory
        inactive_dir = self.config.inactive_mods_directory

        # Dictionary to store mods by name
        mods_dict: dict[str, Mod] = {}

        # Ensure inactive directory exists
        inactive_dir.mkdir(parents=True, exist_ok=True)

        # Scan inactive mods directory to discover all available mods
        if inactive_dir.exists():
            for item in inactive_dir.iterdir():
                # Only process directories
                if not item.is_dir():
                    continue

                name = item.name
                if name not in mods_dict:
                    mods_dict[name] = Mod(
                        name=name, file_path=item, enabled=False, priority=None
                    )

        # Get the active mods list from the current profile config
        current_profile_name = self.config.current_profile
        if current_profile_name not in self.config.profiles:
            from ..models.config import Profile
            self.config.profiles[current_profile_name] = Profile()

        profile_config = self.config.profiles[current_profile_name]
        active_mods_ordered = profile_config.active

        # Mark mods as enabled based on the config and assign priorities
        priority = 0
        for mod_name in active_mods_ordered:
            if mod_name in mods_dict:
                mods_dict[mod_name].enabled = True
                mods_dict[mod_name].priority = priority
                priority += 1

        # Build sorted list: enabled first (by priority), then disabled (alphabetically)
        enabled_mods = sorted(
            [m for m in mods_dict.values() if m.enabled],
            key=lambda m: m.priority if m.priority is not None else 999999,
        )
        disabled_mods = sorted(
            [m for m in mods_dict.values() if not m.enabled],
            key=lambda m: m.name,
        )

        self.mods = enabled_mods + disabled_mods

        return self.mods

    def _reassign_priorities(self) -> None:
        """Reassign priorities to enabled mods based on their current order."""
        priority = 0
        for mod in self.mods:
            if mod.enabled:
                mod.priority = priority
                priority += 1
            else:
                mod.priority = None

    def toggle_mod(self, index: int) -> None:
        """Toggle a mod's enabled state."""
        if 0 <= index < len(self.mods):
            mod = self.mods[index]
            mod.enabled = not mod.enabled

            # If enabling, move to end of enabled list and assign priority
            if mod.enabled:
                # Remove from current position
                self.mods.pop(index)
                # Find last enabled mod position
                last_enabled_idx = 0
                for i, m in enumerate(self.mods):
                    if m.enabled:
                        last_enabled_idx = i + 1
                # Insert after last enabled mod
                self.mods.insert(last_enabled_idx, mod)
            else:
                # If disabling, move to disabled section
                self.mods.pop(index)
                # Find first disabled mod position
                first_disabled_idx = len(self.mods)
                for i, m in enumerate(self.mods):
                    if not m.enabled:
                        first_disabled_idx = i
                        break
                self.mods.insert(first_disabled_idx, mod)

            self._reassign_priorities()

    def move_up(self, index: int) -> int:
        """
        Move a mod up in the list (decrease priority).

        Returns:
            New index of the mod
        """
        if index > 0 and index < len(self.mods):
            mod = self.mods[index]
            other_mod = self.mods[index - 1]

            # Can only swap within the same enabled/disabled group
            if mod.enabled == other_mod.enabled:
                self.mods[index], self.mods[index - 1] = (
                    self.mods[index - 1],
                    self.mods[index],
                )
                self._reassign_priorities()
                return index - 1

        return index

    def move_down(self, index: int) -> int:
        """
        Move a mod down in the list (increase priority).

        Returns:
            New index of the mod
        """
        if index >= 0 and index < len(self.mods) - 1:
            mod = self.mods[index]
            other_mod = self.mods[index + 1]

            # Can only swap within the same enabled/disabled group
            if mod.enabled == other_mod.enabled:
                self.mods[index], self.mods[index + 1] = (
                    self.mods[index + 1],
                    self.mods[index],
                )
                self._reassign_priorities()
                return index + 1

        return index

    def apply(self) -> None:
        """
        Apply mod changes by:
        1. Cleaning up the active directory (removing mods from other profiles)
        2. Saving the active mods order to the profile config
        3. Copying enabled mod folders to the active directory with priority prefixes
        4. Removing disabled mods from active directory
        """
        # Ensure Default profile exists before any operations
        default_profile_dir = self.config.base_game_directory / "mods" / "Default"
        default_profile_dir.mkdir(parents=True, exist_ok=True)

        # Clean up active directory first (remove mods from other profiles)
        self._cleanup_active_directory()

        active_dir = self.config.active_mods_directory
        inactive_dir = self.config.inactive_mods_directory

        # Ensure active and inactive directories exist
        active_dir.mkdir(parents=True, exist_ok=True)
        inactive_dir.mkdir(parents=True, exist_ok=True)

        # Save the active mods order to the config
        current_profile_name = self.config.current_profile
        if current_profile_name not in self.config.profiles:
            from ..models.config import Profile
            self.config.profiles[current_profile_name] = Profile()

        profile_config = self.config.profiles[current_profile_name]
        profile_config.active = [mod.name for mod in self.mods if mod.enabled]

        # Build set of expected active mod directory names
        expected_active_mods = set()
        for mod in self.mods:
            if mod.enabled:
                expected_active_mods.add(mod.active_dirname)

        # Remove mods that shouldn't be in active directory
        if active_dir.exists():
            for item in active_dir.iterdir():
                if item.is_dir() and item.name not in expected_active_mods:
                    shutil.rmtree(item)

        # Copy enabled mods that aren't already in active directory
        for mod in self.mods:
            if mod.enabled:
                source = inactive_dir / mod.name
                dest = active_dir / mod.active_dirname

                # Only copy if source exists and destination doesn't
                if source.exists() and source.is_dir() and not dest.exists():
                    shutil.copytree(source, dest)

    def get_mod_at(self, index: int) -> Mod | None:
        """Get mod at specific index."""
        if 0 <= index < len(self.mods):
            return self.mods[index]
        return None

    def set_mod_enabled(self, index: int, enabled: bool) -> None:
        """Set a mod's enabled state."""
        if 0 <= index < len(self.mods):
            mod = self.mods[index]
            if mod.enabled != enabled:
                self.toggle_mod(index)
