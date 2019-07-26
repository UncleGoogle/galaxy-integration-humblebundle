import argparse
import sys
import psutil
import json
import os
import subprocess
import shutil
from pathlib import Path
from distutils.dir_util import copy_tree
from glob import glob

from src.version import __version__
from config import REQUIREMENTS, GALAXY_PATH, DIST_PLUGIN

gapi = Path(__file__) / '..' / 'galaxy-integrations-python-api' / 'src'
sys.path.append(str(gapi.resolve()))
import galaxy.tools


parser = argparse.ArgumentParser()
parser.add_argument("command", choices=["install", "build", "dist", "test", "copy", "release"])
parser.add_argument("-o", "--output", help="build destination")


def install():
    subprocess.run(["pip", "install", "-r", REQUIREMENTS])


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
        "version": __version__,
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
            for child in proc.children():
                child.terminate()
            proc.terminate()
            break
    else:
        print('Galaxy instance not found.')

    build(output)

    print(f'Reopening Galaxy from {galaxy_path}')
    subprocess.run([galaxy_path])


def copy(output=DIST_PLUGIN, galaxy_path=GALAXY_PATH):
    print('copying source code ...')
    for file_ in glob("src/*.py"):
        shutil.copy(file_, output)


def test():
    subprocess.run(["pytest"])


def release():
    zip_name = f'humblebundle_{__version__}'
    wd = Path(__file__).parent
    tmp_build_dir = wd / zip_name

    arch = wd / zip_name
    if arch.exists():
        if input(f'{str(arch)} already exists. Proceed? y/n') !='y':
            return

    build(str(tmp_build_dir))
    shutil.make_archive(zip_name, 'zip', root_dir=wd, base_dir=tmp_build_dir)
    shutil.rmtree(tmp_build_dir)


    tag = 'v' + __version__
    print('creating and pushing to origin tag: ', tag)
    subprocess.run(['git', 'tag', tag])
    subprocess.run(['git', 'push', 'origin', tag])
    # TODO: publish on github


def main():
    args = parser.parse_args()
    output = args.output if args.output else DIST_PLUGIN
    if args.command == 'install':
        install()
    elif args.command == 'build':
        build(output)
    elif args.command == 'dist':
        dist(output)
    elif args.command == 'copy':
        copy(output)
    elif args.command == 'test':
        test()
    elif args.command == 'release':
        release()
    else:
        print(f'command {args.command} not exits')


if __name__ == "__main__":
    main()
