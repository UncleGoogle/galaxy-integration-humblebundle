## Version 0.7.0

[Added]

- Graphical User Interface for configuration window.
    It can be opened by clicking "Install" button on any Humble game.

- Ability to import predefined tags: `Key`, `Unrevealed` and `Trove` to library. 
    This won't add tags for newly appeared games automatically. You have to reimport them manually by going to Settings -> Features -> Import button under "HUMBLE BUNDLE".

- Support for keys containing multiple games at once.


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