# crossworlds-modmanager

[![PyPI - Version](https://img.shields.io/pypi/v/crossworlds-modmanager.svg)](https://pypi.org/project/crossworlds-modmanager)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/crossworlds-modmanager.svg)](https://pypi.org/project/crossworlds-modmanager)

-----

Sonic Racing CrossWorlds Mod Manager

## Table of Contents

- [Installation](#installation)
- [License](#license)

## Installation

```console
pipx install crossworlds-modmanager
```

### MIME Handler Registration

The application can be registered as a handler for `crosspatch://` URLs, allowing users to click crosspatch links in their browser and have them automatically open in the mod manager.

After installing the application with pip or pipx, run:

```sh
# Register the MIME handler
crossworlds-modmanager-register

# To unregister later (before uninstalling)
crossworlds-modmanager-unregister
```

## License

`crossworlds-modmanager` is distributed under the terms of the [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.en.html) license.
