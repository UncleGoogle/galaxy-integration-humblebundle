## Version 0.11.0
[Added]
- Humble App Support - install, launch, uninstall, getting game size andinstallation state

Collection and Vault games are shown under Subscriptions tab in separate categories.
How to set bookmark, see:
https://github.com/UncleGoogle/galaxy-integration-humblebundle/#recommended-humble-choice-view

[Fixed]
- Adjusting to humble API changes in May 2022 #183
- Error handling in case of authorisation cookie invalidation #179

## Version 0.10.0

[Fixed]
- Error handling bug introduced in 0.9.5
- Rework getting subscriptions list #165 #167
- Adjust to new Choice subscription model introduced on March 2022 #172 
- Update and re-set sentry sdk
- Not showing choice month games if there was no extras list (eg. Humble Choice 12-2021)

[Changed]
- Use new bulk API for fetching orders list #168 
- Move the last Choice month to the top of subscription list in Galaxy Settings>Features window

[Removed]
- Trove support (Humble Choice Collection suppport is planned in the future)

## Version 0.9.5
(!) WARNING: If you're Humble subscriber, plugin reconnection is needed to sync subscriptions again (!)

[Fixed]
- Error while loading a subscriptions list (humble choice and Trove games not visible) #161
- Multi-game keys from bundles: no longer returns game title with leading "and" #157 @ 5dd53f0 by @Gwindalmir
- Mutli-game keys from bundles: list of games titles that should not be splitted is now case insensitive #157 @ d95cd550 by @Gwindalmir
- GUI: misleading tooltip information @ f96edbd

## Version 0.9.4
(!) WARNING: If you're Humble subscriber, plugin reconnection is needed to sync subscriptions again (!)

[Fixed]
- Plugin being offline for subscribers and no subscriptions shown in Settings->Features #151

## Version 0.9.3

[Fixed]
- Showing choices before pasued months #148

## Version 0.9.2

[Fixed]
- Showing subscriptions (adjusting to changes in humble API again) #139
- Typo in subscription months (thanks @Oxenoth)

## Version 0.9.1

[Fixed]
- Showing subscriptions #136
## Version 0.9.0

[Added]
- Importing game sizes #135
- Info when particular game was added to Trove #134

[Fixed]
- Getting Trove games #133
- Loading GUI on Mac by removing non UTF8 character from CHANGELOG @ 9478b62


## Version 0.8.1
Addressed issues: https://github.com/UncleGoogle/galaxy-integration-humblebundle/milestone/6

[Fixed]
- Not showing games due to unsupported platform id #125 @ 84a7e50
- Splitting multigame key by using blacklist #124
- Show Install button for all keys #132
- Fix failing on parsing installed games when non-local uninstaller is used ("Blades of Avernum" case) #127

## Version 0.8.0

[Added]
- Humble Choice support #108; see how to set Humble Choice bookmark:
https://github.com/UncleGoogle/galaxy-integration-humblebundle#recommended-humble-choice-view

[Changed]
- Trove as subscription #102; trove access is automatically detected but it can be overwritten from Galaxy Settings -> Features
- Installed games detection: limit executable search to root level #119

[Fixed]
- Downloading DRM-free games #97
- Not showing claimed choices #113


## Version 0.7.1

[Fixed]
- GUI: fix showing (add missing changelog) on stable branch
- psutil: security update to 5.6.6

[Changed]
- GUI: rate of loading library settings decreased to ~0.3/sec to protect Galaxy from expensive operations #91

## Version 0.7.0

[Added]
- Graphical User Interface for configuration. It can be opened by double clicking "Install" button on any Humble game.
- Ability to import predefined tags: `Key`, `Unrevealed` and `Trove` to library. This won't add tags for newly appeared games automatically. You have to reimport them manually by going to Settings -> Features -> Import button under "HUMBLE BUNDLE".
- Support for keys containing multiple games at once.
- Automatic updates to integration downloaded manually from https://github.com/UncleGoogle/galaxy-integration-humblebundle/releases (this is "latest" version channel - new versions come eariler but are less stable than integrtion downloaded via Galaxy)

## Version 0.6.0

[Added]
- Config: open config by double clicking "Install" button of any HumbleBundle game (#74)
- Trove: get (scrap) ALL recent games (previously only humble trove API was used in which most recent games appears with a week or two delay (#79)

[Changed]
- Config: config file was moved outside of the plugin code (#80) to:
    - Windows: `%LocalAppData%/galaxy-hb/galaxy-humble-config.ini`
    - Mac: `~/.config/galaxy-humble.cfg`
- Config: dropped caching previous config (no need now)

[Fixed]
- Fix "no loading library" bug caused by titles longer than 100chars (#76)
- Fix plugin crashes (IndexError) while checking installed games (eg. when game "Caffeine" was installed) (#77)
- Fix release job (#72)