# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

from pathlib import Path
from pydantic import BaseModel, Field


class Mod(BaseModel):
    """Represents a UE5 mod (a directory containing .pak files)."""

    name: str = Field(..., description="The mod name without priority prefix")
    file_path: Path = Field(..., description="Path to the mod directory")
    enabled: bool = Field(default=False, description="Whether the mod is enabled")
    priority: int | None = Field(
        default=None, description="Load priority (lower = earlier)"
    )

    @property
    def display_name(self) -> str:
        """Return the display name for the mod."""
        return self.name

    @property
    def active_dirname(self) -> str:
        """Return the directory name with priority prefix for active mods."""
        if self.priority is not None:
            return f"{self.priority:03d}.{self.name}"
        return self.name

    @staticmethod
    def parse_dirname(dirname: str) -> tuple[str, int | None]:
        """
        Parse a mod directory name to extract the name and priority.

        Args:
            dirname: The directory name (e.g., "001.mod-name" or "mod-name")

        Returns:
            Tuple of (mod_name, priority or None)
        """
        # Check if dirname starts with a priority prefix (###.)
        parts = dirname.split(".", 1)
        if len(parts) == 2 and len(parts[0]) == 3 and parts[0].isdigit():
            priority = int(parts[0])
            name = parts[1]
            return name, priority
        return dirname, None

    class Config:
        arbitrary_types_allowed = True
