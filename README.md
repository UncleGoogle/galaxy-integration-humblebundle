# galaxy-integration-humblebundle

Integration for GOG Galaxy 2.0.

## Features

This plugin is currenly in early development stage.

* Listing DRM free games from HumbleBundle library (those with downloads for Windows, MacOS or Linux)
* Simple download

## Installation

Unpack `humblebundle_v{}.zip` asset from latest [release][1] to:
- (WINDOWS) `%localappdata%\GOG.com\Galaxy\plugins\installed`
- (MACOS) `~/Library/Application Support/GOG.com/Galaxy/plugins/installed`

or build from source code (python3.6 or higher required):

1. `git clone --recursive https://github.com/UncleGoogle/galaxy-integration-humblebundle.git`
2. `cd galaxy-integration-humblebundle`
3. `python tasks.py install`
4. `python tasks.py dist`

[1]: https://github.com/UncleGoogle/galaxy-integration-humblebundle/releases
