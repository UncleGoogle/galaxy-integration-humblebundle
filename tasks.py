import argparse
import sys
import psutil
import json
import os
import pathlib
import subprocess
from shutil import rmtree, copy
from glob import glob

from src.version import __version__


REQUIREMENTS = 'requirements.txt'
if sys.platform == 'win32':
    GALAXY_PATH = 'D:\Program Files (x86)\GOG Galaxy\GalaxyClient.exe'
    DIST_DIR = os.environ['localappdata'] + '\GOG.com\Galaxy\plugins\installed'
elif sys.platform == 'darwin':
    GALAXY_PATH = "/Applications/GOG Galaxy.app/Contents/MacOS/GOG Galaxy"
    DIST_DIR = os.environ['HOME'] + r"/Library/Application\ Support/GOG.com/Galaxy/plugins/installed"
DIST_PLUGIN = os.path.join(DIST_DIR, 'humblebundle')

parser = argparse.ArgumentParser()
parser.add_argument("command")
args = parser.parse_args()

def install():
    subprocess.run(["pip", "install", REQUIREMENTS])

def build(output=DIST_PLUGIN):
    if os.path.exists(output):
        rmtree(output)

    # install dependencies
    args = [
        "pip", "install",
        "-r", REQUIREMENTS,
        "--target", output,
        "--implementation", "cp",
        "--python-version", "37",
        "--no-compile",
        "--no-deps"
    ]
    print('running', args)
    subprocess.run(args)

    # copy source
    for file_ in glob("src/*.py"):
        copy(file_, output)

    # create manifest
    manifest = {
        "name": "Humble Bundle plugin",
        "platform": "humble",
        "guid": "f0ca3d80-a432-4d35-a9e3-60f27161ac3a",
        "version": __version__,
        "description": "GOG Galaxy 2.0 integration",
        "author": "Mesco",
        "email": "mieszkoziemowit@gmail.com",
        "url": "",
        "script": "plugin.py"
    }
    with open(os.path.join(output, "manifest.json"), "w") as file_:
        json.dump(manifest, file_, indent=4)

def dist(output=DIST_PLUGIN, galaxy_path=GALAXY_PATH):
    for proc in psutil.process_iter(attrs=['exe'], ad_value=''):
        if proc.info['exe'] == galaxy_path:
            print(f'Galaxy at {galaxy_path} is running!. Terminating...')
            proc.terminate()
    else:
        print('Galaxy instance not found.')

    build(output)

    print(f'Reopening Galaxy from {galaxy_path}')
    subprocess.run([galaxy_path])

def test():
    subprocess.run(["pytest"])

def main():
    if args.command == 'install':
        install()
    elif args.command == 'build':
        build()
    elif args.command == 'dist':
        dist()
    elif args.command == 'test':
        test()

if __name__ == "__main__":
    main()





