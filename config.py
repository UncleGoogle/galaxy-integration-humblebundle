import sys
import os


REQUIREMENTS = os.path.join('requirements', 'app.txt')

if sys.platform == 'win32':
    GALAXY_PATH = 'C:\\Program Files (x86)\\GOG Galaxy\\GalaxyClient.exe'
    DIST_DIR = os.environ['localappdata'] + '\\GOG.com\\Galaxy\\plugins\\installed'
elif sys.platform == 'darwin':
    GALAXY_PATH = "/Applications/GOG Galaxy.app/Contents/MacOS/GOG Galaxy"
    DIST_DIR = os.environ['HOME'] + r"/Library/Application\ Support/GOG.com/Galaxy/plugins/installed"

DIST_PLUGIN = os.path.join(DIST_DIR, 'humblebundle')
