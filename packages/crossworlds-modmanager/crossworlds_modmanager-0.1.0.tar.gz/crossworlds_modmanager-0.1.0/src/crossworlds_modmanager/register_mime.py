# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

"""Script to register crosspatch:// MIME handler."""

import sys
import subprocess
import shutil
from pathlib import Path


def register_linux():
    """Register crosspatch:// handler on Linux."""
    try:
        # Find the executable path
        exec_path = shutil.which("crossworlds-modmanager")
        if not exec_path:
            print("Warning: crossworlds-modmanager executable not found in PATH")
            return False

        # Create .desktop file content
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Crossworlds Mod Manager
Comment=Manage mods for Crossworlds
Exec={exec_path} %u
Terminal=false
Categories=Game;Utility;
MimeType=x-scheme-handler/crosspatch;
"""

        # Write to user's applications directory
        apps_dir = Path.home() / ".local" / "share" / "applications"
        apps_dir.mkdir(parents=True, exist_ok=True)
        desktop_file = apps_dir / "crossworlds-modmanager.desktop"

        desktop_file.write_text(desktop_content)
        print(f"Created desktop file: {desktop_file}")

        # Update desktop database
        subprocess.run(
            ["update-desktop-database", str(apps_dir)], capture_output=True, check=False
        )

        # Register as default handler for crosspatch://
        subprocess.run(
            [
                "xdg-mime",
                "default",
                "crossworlds-modmanager.desktop",
                "x-scheme-handler/crosspatch",
            ],
            capture_output=True,
            check=False,
        )

        print("Successfully registered crosspatch:// handler on Linux")
        return True

    except Exception as e:
        print(f"Error registering on Linux: {e}")
        return False


def register_windows():
    """Register crosspatch:// handler on Windows."""
    try:
        import winreg

        # Find the executable path
        exec_path = shutil.which("crossworlds-modmanager")
        if not exec_path:
            print("Warning: crossworlds-modmanager executable not found in PATH")
            return False

        # Create registry keys
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER, r"Software\Classes\crosspatch"
        ) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "URL:Crosspatch Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

        command_key_path = r"Software\Classes\crosspatch\shell\open\command"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, f'"{exec_path}" "%1"')

        print("Successfully registered crosspatch:// handler on Windows")
        return True

    except ImportError:
        print("Error: winreg module not available (not on Windows)")
        return False
    except Exception as e:
        print(f"Error registering on Windows: {e}")
        return False


def main():
    """Main registration function."""
    print("Registering crosspatch:// MIME handler...")

    if sys.platform == "linux":
        success = register_linux()
    elif sys.platform == "win32":
        success = register_windows()
    else:
        print(f"Unsupported platform: {sys.platform}")
        print("Manual registration required.")
        success = False

    if success:
        print("\nMIME handler registered successfully!")
        print("You can now click crosspatch:// links in your browser")
        print("to open them directly in Crossworlds Mod Manager.")
    else:
        print("\nMIME handler registration failed or incomplete.")
        print("You may need to register manually. See CLAUDE.md for instructions.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
