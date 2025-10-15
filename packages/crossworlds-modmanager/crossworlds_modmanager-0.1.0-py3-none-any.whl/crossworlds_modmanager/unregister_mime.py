# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

"""Script to unregister crosspatch:// MIME handler."""

import sys
import subprocess
from pathlib import Path


def unregister_linux():
    """Unregister crosspatch:// handler on Linux."""
    try:
        # Remove desktop file
        desktop_file = (
            Path.home()
            / ".local"
            / "share"
            / "applications"
            / "crossworlds-modmanager.desktop"
        )
        if desktop_file.exists():
            desktop_file.unlink()
            print(f"Removed desktop file: {desktop_file}")

        # Update desktop database
        apps_dir = Path.home() / ".local" / "share" / "applications"
        subprocess.run(
            ["update-desktop-database", str(apps_dir)], capture_output=True, check=False
        )

        print("Successfully unregistered crosspatch:// handler on Linux")
        return True

    except Exception as e:
        print(f"Error unregistering on Linux: {e}")
        return False


def unregister_windows():
    """Unregister crosspatch:// handler on Windows."""
    try:
        import winreg

        # Delete registry keys
        try:
            winreg.DeleteKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Classes\crosspatch\shell\open\command",
            )
            winreg.DeleteKey(
                winreg.HKEY_CURRENT_USER, r"Software\Classes\crosspatch\shell\open"
            )
            winreg.DeleteKey(
                winreg.HKEY_CURRENT_USER, r"Software\Classes\crosspatch\shell"
            )
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\crosspatch")
            print("Successfully unregistered crosspatch:// handler on Windows")
            return True
        except FileNotFoundError:
            print("crosspatch:// handler was not registered")
            return True

    except ImportError:
        print("Error: winreg module not available (not on Windows)")
        return False
    except Exception as e:
        print(f"Error unregistering on Windows: {e}")
        return False


def main():
    """Main unregistration function."""
    print("Unregistering crosspatch:// MIME handler...")

    if sys.platform == "linux":
        success = unregister_linux()
    elif sys.platform == "win32":
        success = unregister_windows()
    else:
        print(f"Unsupported platform: {sys.platform}")
        success = False

    if success:
        print("\nMIME handler unregistered successfully!")
    else:
        print("\nMIME handler unregistration failed or incomplete.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
