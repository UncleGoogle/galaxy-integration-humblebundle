## Unreleased

[Changed]
- Installed games detection: limit executable search to root level #119


## Version 0.8.0 Alpha (pre-release)
[Fixed]
- Downloading DRM-free games #97
- Not showing claimed choices #113

[Added]
- Humble Choice support #108

[Changed]
- Trove as subscription #102; trove access is automatically detected but it can be overwritten from Galaxy Settings -> Features


## Version 0.7.1

[Fixed]
- GUI: fix showing (add missing changelog) on stable branch
- psutil: security update to 5.6.6

[Changed]
- GUI: rate of loading library settings decreased to ~0.3/sec to protect Galaxy from expensive operations #91

## Version 0.7.0

[Added]
- Graphical User Interface for configuration. It can be opened by double clicking "Install" button on any Humble game.
- Ability to import predefined tags: `Key`, `Unrevealed` and `Trove` to library. This won't add tags for newly appeared games automatically. You have to reimport them manually by going to Settings -> Features -> Import button under "HUMBLE BUNDLE".
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