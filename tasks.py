import argparse
import psutil
import json
import os
import subprocess
import shutil
from distutils.dir_util import copy_tree
from glob import glob

from src.version import __version__
from config import REQUIREMENTS, GALAXY_PATH, DIST_PLUGIN



parser = argparse.ArgumentParser()
parser.add_argument("command")


def install():
    subprocess.run(["pip", "install", REQUIREMENTS])

def build(output=DIST_PLUGIN):
    print('removing', output)
    if os.path.exists(output):
        shutil.rmtree(output)

    args = [
        "pip", "install",
        "-r", REQUIREMENTS,
        "--target", output,
        # "--implementation", "cp",
        # "--python-version", "37",
        # "--no-deps"
    ]
    print(f'running `{" ".join(args)}`')
    subprocess.check_call(args)

    print('copying source code ...')
    for file_ in glob("src/*.py"):
        shutil.copy(file_, output)

    print('copying galaxy api ...')
    copy_tree("galaxy-integrations-python-api/src", output)

    print('creating manifest ...')
    manifest = {
        "name": "Humble Bundle plugin",
        "platform": "humble",
        "guid": "f0ca3d80-a432-4d35-a9e3-60f27161ac3a",
        "version": str(__version__),
        "description": "GOG Galaxy 2.0 integration",
        "author": "Mesco",
        "email": "mieszkoziemowit@gmail.com",
        "url": "https://github.com/UncleGoogle/galaxy-integration-humblebundle/",
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
    args = parser.parse_args()
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





