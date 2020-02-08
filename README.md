# galaxy-integration-humblebundle

Integration for GOG Galaxy 2.0.

## Features

* Library:
    * DRM free direct downloads from HumbleBundle
    * Third party game keys
    * Humble Trove games
* Install: simple download via webbrowser
* Installed games detection:
    * scanning Windows registry (only for games that can be uninstalled via `Control Panel\Programs\Programs and Features`)
    * scanning file directory trees given in config file (experimental - 1 level deep tree search for directories names similar to game names from library)
* Launch: running games tracking (only if launched via Galaxy)

## Installation

Download asset `humblebundle_v{}.zip` from [releases][1] and upack to:
- Windows: `%localappdata%\GOG.com\Galaxy\plugins\installed`
- MacOS: `~/Library/Application Support/GOG.com/Galaxy/plugins/installed`

or build from source code (requires `python3.6` or higher):

1. `git clone --recursive https://github.com/UncleGoogle/galaxy-integration-humblebundle.git`
2. `cd galaxy-integration-humblebundle`
3. `pip install -r requirements-dev.txt`
4. `inv dist`

## Configuration

Edit your local [config.ini](src/config.ini)

## Tags

You can import predefined tags: `Key`, `Unrevealed` and `Trove` to your library manually by going to
`Settings` -> `Features` -> `Import` button under "HUMBLE BUNDLE".

Warning: this will not automatically add tags for newly added games. You will have to import tags again.

#### Defaults:
- Library: List DRM-free games and unrevealed third party keys
- Installed games: use only Windows registry scan; edit `search_paths` to enable directory scaning feature

## Bug Reporting
This integrations uses sentry.io to report anonymous error reports.
Personal and sensitive data are not gathered.

## Acknowledgements
- https://github.com/gogcom/galaxy-integrations-python-api
- https://github.com/MayeulC/hb-downloader

[1]: https://github.com/UncleGoogle/galaxy-integration-humblebundle/releases
