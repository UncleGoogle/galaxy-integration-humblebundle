# galaxy-integration-humblebundle

Integration for GOG Galaxy 2.0.

## Features

* Library: listing DRM free games from HumbleBundle library (those with downloads for Windows, MacOS or Linux)
* Library: Humble Trove support
* Install: simple download via webbrowser
* Launch: only Windows games installed via __installer__ are detected
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

- cannot detect game as installed if it has proper installer. Sadly, many HB games are self-running
- no launch support for macOS yet

## See also
- https://github.com/gogcom/galaxy-integrations-python-api
- https://github.com/MayeulC/hb-downloader

[1]: https://github.com/UncleGoogle/galaxy-integration-humblebundle/releases
