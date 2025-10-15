# SPDX-FileCopyrightText: 2025-present Yiannis Charalambous <yiannis128@hotmail.com>
#
# SPDX-License-Identifier: AGPL-3.0

import sys
import logging
from PySide6.QtWidgets import QApplication
from .ui import MainWindow


def main() -> int:
    """Main entry point for the application."""
    # Configure logging to stdout
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Crossworlds Mod Manager")
    app.setOrganizationName("Crossworlds")
    app.setOrganizationDomain("crossworlds-modmanager")

    # Check if a crosspatch URL was passed as argument
    crosspatch_url = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        # Check if it's a crosspatch URL
        if arg.startswith("crosspatch:") or "gamebanana.com/dl/" in arg:
            crosspatch_url = arg
            print(f"[Main] Launched with URL: {crosspatch_url}")
            logging.info(f"Launched with URL: {crosspatch_url}")

    # Create and show main window
    window = MainWindow(initial_download_url=crosspatch_url)
    window.show()

    # Run event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
