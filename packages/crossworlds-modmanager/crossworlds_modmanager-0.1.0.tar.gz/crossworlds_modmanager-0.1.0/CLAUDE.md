# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based mod manager for Crossworlds, built using the Hatch build system. The project uses PySide6 (Qt6) for cross-platform GUI support on Linux and Windows.

## Build System

This project uses Hatch as its build/project management tool. Key characteristics:
- Package source: `src/crossworlds_modmanager/`
- Tests directory: `tests/`
- Version is dynamically read from `src/crossworlds_modmanager/__about__.py`
- Python 3.8+ required

## Common Commands

### Development Environment
```bash
# Install dependencies in default environment
hatch env create

# Run the application
hatch run crossworlds-modmanager

# Or run directly with Python
hatch run python -m crossworlds_modmanager.main

# Install in editable mode for development
pip install -e .
```

### Testing
```bash
# Run tests (when test framework is added)
hatch run pytest

# Run tests with coverage
hatch run pytest --cov=src/crossworlds_modmanager
```

### Type Checking
```bash
# Run mypy type checker
hatch run types:check

# Type check specific files
hatch run types:check src/crossworlds_modmanager/module.py
```

### Building and Publishing
```bash
# Build distribution packages
hatch build

# Clean build artifacts
hatch clean

# Publish to PyPI (requires credentials)
hatch publish
```

## Architecture Notes

### Application Structure (Three-Layer Architecture)

The application follows a clean separation of concerns:

1. **Data Layer** (`models/`)
   - `Mod`: Represents a UE5 mod with priority and enabled state
   - `AppConfig`: Application configuration (uses Pydantic)
   - `ConfigManager`: Handles loading/saving config from `~/.config/crossworlds-modmanager/config.toml`

2. **Business Logic Layer** (`services/`)
   - `ModManager`: Core mod management logic
     - Scans active/inactive mod directories for mod folders
     - Handles mod activation/deactivation
     - Manages load order via priority prefixes on directory names (e.g., `001.mod-name`)
     - Applies changes by copying mod directories to active directory
   - `ModDownloader`: Async mod downloading from GameBanana
     - Supports both direct URLs (`gamebanana.com/dl/{file_id}`) and crosspatch MIME links
     - Downloads files with progress tracking (QThread-based)
     - Automatically extracts archives to inactive mods directory
   - `ArchiveExtractor`: Multi-format archive extraction
     - Supports ZIP, 7Z, and RAR formats
     - Automatically detects archive type from file extension
     - Provides unified extraction interface

3. **UI Layer** (`ui/`)
   - `MainWindow`: Main application window with tabs
   - `ModsTab`: List of mods with checkboxes and action buttons
   - `DownloadTab`: Async mod downloading interface
     - Paste GameBanana URLs (direct or crosspatch format)
     - Real-time progress tracking with progress bar
     - Cancel download functionality
     - Disables tab switching during download
   - `SettingsTab`: Configuration interface

### UE5 Mod Management

- **Mod structure**: Mods are represented as directories containing `.pak` files
- **Active mods directory**: `{base_game_directory}/UNION/Content/Paks/~mods`
- **Inactive mods directory**: `{base_game_directory}/mods`
- **Load order**: UE5 loads mods alphabetically, so priority is enforced via `###.` prefix on directory names
- **Apply operation**: Copies enabled mod directories from inactive directory to active directory with priority prefix
- **Cleanup**: On refresh, any mod directories in active directory without valid `###.` prefix are moved to inactive directory

### UI Framework
- Uses PySide6 (Qt6 bindings) for cross-platform GUI
- Supports both Linux and Windows natively
- Qt provides native look-and-feel on each platform

### Package Structure
- Entry point: `src/crossworlds_modmanager/main.py`
- Version management: `src/crossworlds_modmanager/__about__.py`
- Tests mirror source structure under `tests/`

## Coverage Configuration

Coverage is configured to:
- Track both `crossworlds_modmanager` package and `tests`
- Use branch coverage
- Exclude `__about__.py` from coverage reports
- Exclude type checking blocks and `if __name__ == "__main__"` blocks

## MIME Handler Registration

The application can be registered as a handler for `crosspatch://` URLs, allowing users to click crosspatch links in their browser and have them automatically open in the mod manager.

### Automatic Registration (After Installation)

After installing the application with pip or pipx, run:

```bash
# Register the MIME handler
crossworlds-modmanager-register

# To unregister later
crossworlds-modmanager-unregister
```

### Manual Registration

#### Linux

1. The registration script creates a `.desktop` file at:
   `~/.local/share/applications/crossworlds-modmanager.desktop`

2. The handler is registered with:
   ```bash
   xdg-mime default crossworlds-modmanager.desktop x-scheme-handler/crosspatch
   ```

3. To manually unregister:
   ```bash
   rm ~/.local/share/applications/crossworlds-modmanager.desktop
   update-desktop-database ~/.local/share/applications
   ```

#### Windows

1. The registration script creates registry keys under:
   `HKEY_CURRENT_USER\Software\Classes\crosspatch`

2. Alternatively, you can import the provided registry file:
   - Locate: `resources/register-crosspatch-windows.reg`
   - Update the executable path in the file
   - Double-click to import

3. To manually unregister, delete the registry key or run:
   ```bash
   crossworlds-modmanager-unregister
   ```

### How It Works

1. When a `crosspatch://` link is clicked in the browser, the OS launches:
   ```
   crossworlds-modmanager "crosspatch:https://gamebanana.com/mmdl/..."
   ```

2. The application detects the URL argument in `main.py`

3. The Download tab is automatically opened with the URL pre-filled

4. User can click "Download" to start downloading the mod
