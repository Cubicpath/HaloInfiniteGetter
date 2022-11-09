# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Update Checker
    - Popup that appears when a newer version is released
        - This allows you to seamlessly upgrade to the newest version without a command line using
        the `Upgrade and Restart` button
        - It can be turned off by pressing the `Ignore All` button
- Changelog Viewer
    - Open it through the `Changelog` action in the `Help` context menu
    - Ability to see the latest version in **bold**

### Changed
- Optimized RecursiveSearch (SCAN)

### Fixed
- RecursiveSearch (SCAN) scanning the same json document multiple times


## [0.12] - 2022-11-3 - [PyPI](https://pypi.org/project/hi-getter/0.12/)
### Added
- `CHANGELOG.md`
- `py7zr` dependency
- Menu fade in/out animations
- Cache Explorer, from [gh-29](https://github.com/Cubicpath/HaloInfiniteGetter/pull/29)
    - Able to view file type, size, date modified
    - Opening files in:
        - Output Views
        - Default App
        - Explorer
  - Live-view of the file structure
  - Basic folding controls (ex: Collapse, Expand Recursively)
  - Copying of both the file path and contents
  - Deletion of both files and directories
- Cache importing and exporting, from [gh-35](https://github.com/Cubicpath/HaloInfiniteGetter/pull/35)
    - 7Zip Archives (`*.7z`)
    - ZIP Files (`*.zip` & `*.piz`)
    - TAR Files (`*.tar`, `*.tar.gz`, `*.tgz`, `*.tar.bz2`, `*.tbz2`, `*.tar.xz`, `*.txz`)
        - `gzip`, `bzip2`, and `xz` are the supported compression algorithms

### Changed
- Cache Explorer `Open in Default App` now shows the default icon for the file
- `PySide6` version to 6.4.0

### Fixed
- [gh-31](https://github.com/Cubicpath/HaloInfiniteGetter/issues/31)
- [gh-33](https://github.com/Cubicpath/HaloInfiniteGetter/issues/33)


## [0.12a1] - 2022-10-14 - [PyPI](https://pypi.org/project/hi-getter/0.12a1/)
### Added
- Cache Explorer, from [gh-29](https://github.com/Cubicpath/HaloInfiniteGetter/pull/29)
    - Able to view file type, size, date modified
    - Opening files in:
        - Output Views
        - Default App
        - Explorer
  - Live-view of the file structure
  - Basic folding controls (ex: Collapse, Expand Recursively)
  - Copying of both the file path and contents
  - Deletion of both files and directories


## [0.11.1] - 2022-09-30 - [PyPI](https://pypi.org/project/hi-getter/0.11.1/)
### Added
- Translations to Dropdown Menus
- Relative links to README viewer

### Changed
- Create windows during application startup for performance
- `PySide6` version to 6.3.2
- `python-dotenv` version to 0.21.0

### Fixed
- Linux `Create Shortcut` implementation


## [0.11] - 2022-08-11 - [PyPI](https://pypi.org/project/hi-getter/0.11/)
### Added
- `pyshortcuts` functionality is now natively implemented
- License viewer dropdown, which contains all non-testing requirements
- `About Qt` section in the `Help` menu
- Recursive language key evaluation
- Language inheritance

### Changed
- Very large restructure of project packages
- Transition from `setuptools` to `flit`
- Updated icons, allowing theme-specific icons
- Updated builtin theme syntax in `settings.toml`

### Removed
- `pyshortcuts` dependency
- All possible dependencies to `pywin32` and `win32con`

## [0.10] - 2022-06-29 - [PyPI](https://pypi.org/project/hi-getter/0.10/)
### Added
- Default application icon
- Exception Logger and Status bar
- Asynchronous application network requests
- Ability to dynamically change language during runtime

### Changed
- Move from `PySide6` to `PySide6-Essentials` (much lower download size)
- `python-dotenv` is now a soft-requirement
- `PySide6` version to 6.3.1
- Network stack from `requests` to `QNetwork`

### Removed
- `requests` dependency


## [0.10a2] - 2022-06-22 - [PyPI](https://pypi.org/project/hi-getter/0.10a2/)
### Added
- Default application icon

### Changed
- `python-dotenv` is now a soft-requirement
- `PySide6` version to 6.3.1
- Network stack from `requests` to `QNetwork`

### Removed
- `requests` dependency


## [0.10a1] - 2022-05-08 - [PyPI](https://pypi.org/project/hi-getter/0.10a1/)
### Added
- Exception Logger and Status bar
- Asynchronous application network requests
- Ability to dynamically change language during runtime

### Changed
- `PySide6` version to 6.3.0


## [0.9.2] - 2022-04-09 - [PyPI](https://pypi.org/project/hi-getter/0.9.2/)
### Added
- More HTTP error descriptions
- Many requirements for the upcoming exception reporter

### Fixed
- [gh-12](https://github.com/Cubicpath/HaloInfiniteGetter/issues/12)


## [0.9.1] - 2022-04-02 - [PyPI](https://pypi.org/project/hi-getter/0.9.1/)
### Changed
- Move default settings from a hardcoded value to `resources/default_settings.toml`

### Fixed
- [gh-11](https://github.com/Cubicpath/HaloInfiniteGetter/issues/11)


## [0.9] - 2022-03-30 - [PyPI](https://pypi.org/project/hi-getter/0.9/)
### Added
- README Viewer which displays text from `README.md` with rich markdown rendering
    - As `README.md` is not distributed normally using twine,
      it is read from the installed package's `Description` metadata tag
- First-launch dialog

### Changed
- Make `token` and `wpauth` config files hidden

### Fixed
- Some translations


## [0.8.2] - 2022-03-22 - [PyPI](https://pypi.org/project/hi-getter/0.8.2/)
### Added
- URL in failing error text

### Fixed
- [gh-5](https://github.com/Cubicpath/HaloInfiniteGetter/issues/5)


## [0.8.1] - 2022-03-20 - [PyPI](https://pypi.org/project/hi-getter/0.8.1/)
### Added
- Installing via pip now creates an executable script in PATH (`hi_getter`)
- Use of arrow keys to navigate path history

### Changed
- Only show packages in the About popup if they are installed

### Fixed
- Output button texts


## [0.8] - 2022-03-18 - [PyPI](https://pypi.org/project/hi-getter/0.8/)
### Added
- Ability to view licenses from required packages
- Start of language keys implementation

### Changed
- License viewer upgraded to rich renderer
    - Clickable URLs


## [0.7] - 2022-03-12 - [PyPI](https://pypi.org/project/hi-getter/0.7/)
### Added
- Automatic API key refresh through `wpauth` tokens
    - This accompanies a new guide in the README.md
- Store `wpauth` tokens and API keys in the users `.config/hi_getter` directory in distinct files.
  They are overwritten as needed.

### Changed
- sub-host and parent path are taken into account during caching


## [0.6.2] - 2022-03-07 - [PyPI](https://pypi.org/project/hi-getter/0.6.2/)
### Added
- Warning for flushing cache
- Desktop shortcut creation tool

### Changed
- Move cache to the .cache directory in the user's home folder
- Allow separate minification of detached windows


## [0.6.1] - 2022-02-20 - [PyPI](https://pypi.org/project/hi-getter/0.6.1/)
### Added
- History dropdown for the input field

### Fixed
- Text output not reattaching correctly


## [0.6] - 2022-02-16 - [PyPI](https://pypi.org/project/hi-getter/0.6/)
### Changed
- Main dependency from PyQt6 to PySide6


## [0.5] - 2022-02-14 - [PyPI](https://pypi.org/project/hi-getter/0.5/)
### Added
- Hyperlinks to text output on detected paths
- Descriptions to error codes


## [0.4.2] - 2022-02-14 - [PyPI](https://pypi.org/project/hi-getter/0.4.2/)
### Changed
- Make Text Output read-only
- Hide key when set

### Fixed
- [gh-3](https://github.com/Cubicpath/HaloInfiniteGetter/issues/3)


## [0.4.1] - 2022-02-11 - [PyPI](https://pypi.org/project/hi-getter/0.4.1/)
### Added
- Uploaded to GitHub


[Unreleased]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.12.1...HEAD
[0.12.1]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.12...v0.12.1
[0.12]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.12a1...v0.12
[0.12a1]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.11.1...v0.12a1
[0.11.1]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.11...v0.11.1
[0.11]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.10...v0.11
[0.10]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.10a2...v0.10
[0.10a2]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.10a1...v0.10a2
[0.10a1]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.9.2...v0.10a1
[0.9.2]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.9...v0.9.1
[0.9]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.8.2...v0.9
[0.8.2]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.8...v0.8.1
[0.8]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.7...v0.8
[0.7]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.6.2...v0.7
[0.6.2]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.6...v0.6.1
[0.6]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.5...v0.6
[0.5]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.4.2...v0.5
[0.4.2]: https://github.com/Cubicpath/HaloInfiniteGetter/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/Cubicpath/HaloInfiniteGetter/releases/tag/v0.4.1.post1
