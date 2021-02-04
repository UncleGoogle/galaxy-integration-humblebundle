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

![Humble Install](resources/Humble_Install.gif)

To open: double click "Install" button from any HumbleBundle game view.

Contains:
- Library settings for game types to show
- Local games settings for installed games detection

### Galaxy settings

![Humble Settings](resources/Humble_Settings.png)

To open: go to Galaxy menu -> `Settings` -> `Features` -> "HUMBLE BUNDLE".

Contains:
- Ability to manualy overwrite detected Choice subscription months and Trove
- Importing predefined tags: `Key`, `Unrevealed` for games that are third party keys
  - **Warning:** this will not automatically add tags for newly added games. You will have to import tags again.
  - **Note:** since v0.8 tag `Trove` is not longer used; re-import to clear out

### Recommended Humble Choice view

1. Go to Humble Bundle bookmark

2. Filter to subscriptions

![Humble Filters](resources/Humble_filters.png)

3. Group by subscriptions

![Humble Group By](resources/Humble_Groupby.png)

3. Bookmark

![Humble bookmarked](resources/Humble_bookmarked.png)

4. Rename a new bookmark with right-click

## FAQ

### Can I group my Humble games and Choice games altogether?

You have to create a new filtered HUble Bungle bookmark, proceeding as follows:

1. Click on the defauit _Humble Bundle_ bookmark: you see only the owned games in this view, and your goals is to have a similar view that list both owned and subscritptions games.

2. Change the view filter selecting the funnel icon, then the Status menu -> and then flagging both _Owned_ and _Subcriptions_

![HumbleBundle_Filters](resources/HumbleBundle_Filters.png)

3. Bookmark the search query you just composed clicking on the small bookmark flag

![Humble bookmarked](resources/Bookmarking.png)

3. The view that you just created will show in the bookmark list as an _Humble Bundle_ duplicate, so you want to rename it. To do so click with right mouse button on the new bookmark itself and select _Rename bookmark_ changing name with something you like as for example _Humble Store & Subsc_.

![Humble Rename Bookmark](resources/Bookmark_rename.png)

4. Now when you select the new bookmark you can view (and search!) both owned and subscription Humble Bundle games.

  ![Hmmble Store and Subsc](resources/Bookmark_renamed.png)

Tip: you can also create an _All games_ bookmark in a similar way to include also subscriptions games as they were owned games.

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
