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
    * scanning file directory trees given in config file (experimental; 1 level deep tree search for directories names similar to game names from library)
* Launch: running games tracking (requires launching via Galaxy)

## Installation

#### Stable release:
_autoupdates to next Stable relase (served as [FriendsOfGalaxy fork][5])_

GOG Galaxy 2.0 go to `Settings`->`Integrations`-> use build-in `Search GitHub` engine

#### Latest release:
_autoupdates to next Latest release (since 0.7.0)_

Download asset `humblebundle_v{}.zip` from [releases][1] and upack to:
- Windows: `%localappdata%\GOG.com\Galaxy\plugins\installed`
- MacOS: `~/Library/Application Support/GOG.com/Galaxy/plugins/installed`

#### From source:
_Requires `python3.6` or higher_

1. `git clone https://github.com/UncleGoogle/galaxy-integration-humblebundle.git`
2. `cd galaxy-integration-humblebundle`
3. `pip install -r requirements-dev.txt`
4. `inv dist`  # this will forcelly restart Galaxy

## Configuration

#### Config window

To open double click "Install" button from any HumbleBundle game view.

<img src="https://i.gyazo.com/b806e5d01590f5c6c48fbe09f9dddb95.gif" width="640" height="300"/>

#### Import Tags

Predefined tags: `Key`, `Unrevealed` can be imported to your library manually by going to
Galaxy menu ->
`Settings` -> `Features` -> `Import` button under "HUMBLE BUNDLE".
<img src="https://i.gyazo.com/14ee4e4665e6ab96eca6adc47f151c5e.png" width="640">

**Warning:** this will not automatically add tags for newly added games. You will have to import tags again.
**Warning:** Since v0.8 tag `Trove` is not longer imported. Re-importing clears `Trove` tag from Trove games.


## Bug Reporting
This integrations uses sentry.io to report anonymous error reports.
Personal and sensitive data are not gathered.

Create new issue [here][2].

## Acknowledgements
- GOG.com for Galaxy and its open source [API][3]
- MayeulC for his fork of [Command-line downloader][4] as a starting point for this integration

[1]: https://github.com/UncleGoogle/galaxy-integration-humblebundle/releases
[2]: https://github.com/UncleGoogle/galaxy-integration-humblebundle/issues/new/choose
[3]: https://github.com/gogcom/galaxy-integrations-python-api
[4]: https://github.com/MayeulC/hb-downloader
[5]: https://github.com/FriendsOfGalaxy/galaxy-integration-humble
