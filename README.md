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

### Config window

<img src="https://i.gyazo.com/b806e5d01590f5c6c48fbe09f9dddb95.gif" width="640" height="300"/>

To open: double click "Install" button from any HumbleBundle game view.

Contains:
- Library settings for game types to show
- Local games settings for installed games detection

### Galaxy settings

<img src="https://i.gyazo.com/21804a7ac7ebffb49d7d810b7d85d0d4.png" width="640">

To open: go to Galaxy menu -> `Settings` -> `Features` -> "HUMBLE BUNDLE".

Contains:
- Ability to manualy overwrite detected Choice subscription months and Trove
- Importing predefined tags: `Key`, `Unrevealed` for games that are third party keys
  - **Warning:** this will not automatically add tags for newly added games. You will have to import tags again.
  - **Note:** since v0.8 tag `Trove` is not longer used; re-import to clear out

### Recommended Humble Choice view

1. Go to Humble Bundle bookmark

2. Filter to subscriptions

<img src="https://i.gyazo.com/eccd333b76e6ac8b948d9b012bd62301.png" width="640">

3. Group by subscriptions

<img src="https://i.gyazo.com/869901d9dc6d730d4744ea11eb7c0b8f.png" width="640">

3. Bookmark

<img src="https://i.gyazo.com/d3cb0876788849a9117f739e3b5d875a.png" width="400">

4. Rename a new bookmark with right-click

## FAQ

### How can I search for games in subscriptions and owned games at the same time?

You have to create an _All games_ bookmark, proceeding as follows:

1. Open the default _Owned games_ bookmark

2. Change the filter selecting both owned games and subcription

  ![Filter Configuration](https://user-images.githubusercontent.com/77177410/106529888-88ca8d00-64eb-11eb-96e2-3c55ff4ddc9b.png)

3. Bookmark the search you just composed

  <img src="https://i.gyazo.com/d3cb0876788849a9117f739e3b5d875a.png" width="400">

4. Now you can normally search the new  _All games_ view as you do with all bookmarks view

  ![All games bookmark](https://user-images.githubusercontent.com/77177410/106821639-d7a82c00-667d-11eb-9ee4-9d15628468fe.png)

   Remember you can change the order of your bookmarks, so probably you want to move your new bookmask on top, just under the _Subscriptions_ default bookmark.

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
