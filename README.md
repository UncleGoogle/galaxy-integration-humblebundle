# galaxy-integration-humblebundle

Integration for GOG Galaxy 2.0.

## Features

* Library: listing DRM free games from HumbleBundle library (those with downloads for Windows, MacOS or Linux)
* Library: Humble Trove support
* Install: simple download via webbrowser
* Launch: autodetect installed games (only visible in `Control Panel\Programs\Programs and Features`)
* Launch: track running games (only if launched via Galaxy)

## Installation

Unpack `humblebundle_v{}.zip` asset from latest [release][1] to:
- (WINDOWS) `%localappdata%\GOG.com\Galaxy\plugins\installed`
- (MACOS) `~/Library/Application Support/GOG.com/Galaxy/plugins/installed`

or build from source code (requires `python3.6` or higher):

1. `git clone --recursive https://github.com/UncleGoogle/galaxy-integration-humblebundle.git`
2. `cd galaxy-integration-humblebundle`
3. `pip install invoke`
4. `inv dist`

## Known Issues

- no detection for games installed via default WindowsInstaller (`Msi` uninstaller)
- no launch support for macOS

## See also
- https://github.com/gogcom/galaxy-integrations-python-api
- https://github.com/MayeulC/hb-downloader

[1]: https://github.com/UncleGoogle/galaxy-integration-humblebundle/releases
