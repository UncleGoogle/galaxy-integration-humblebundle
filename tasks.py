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

from invoke import task

from src.version import __version__
from config import REQUIREMENTS, REQUIREMENTS_DEV, GALAXY_PATH, DIST_PLUGIN

gapi = Path(__file__) / '..' / 'galaxy-integrations-python-api' / 'src'
sys.path.append(str(gapi.resolve()))
import galaxy.tools


@task
def install(c, dev=False):
    if dev:
        c.run("python -m pip install -r " + REQUIREMENTS_DEV)
    else:
        c.run("python -m pip install -r " + REQUIREMENTS)


@task
def build(c, output=DIST_PLUGIN):
    print('removing', output)
    if os.path.exists(output):
        shutil.rmtree(output)

    args = [
        "python", "-m", "pip", "install",
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
    os.mkdir(Path(output) / 'local')
    for file_ in glob("src/local/*.py"):
        shutil.copy(file_, str(Path(output) / 'local'))

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


@task
def dist(c, output=DIST_PLUGIN, galaxy_path=GALAXY_PATH):
    for proc in psutil.process_iter(attrs=['exe'], ad_value=''):
        if proc.info['exe'] == galaxy_path:
            print(f'Galaxy at {galaxy_path} is running!. Terminating...')
            for child in proc.children():
                child.terminate()
            proc.terminate()
            break
    else:
        print('Galaxy instance not found.')

    c.run(f'inv build -o {output}')

    print(f'Reopening Galaxy from {galaxy_path}')
    subprocess.run([galaxy_path])


@task
def copy(c, output=DIST_PLUGIN, galaxy_path=GALAXY_PATH):
    print('copying source code ...')
    for file_ in glob("src/*.py"):
        shutil.copy(file_, output)


@task
def test(c, mypy_target=None):
    c.run("pytest")
    if mypy_target:
        modules = ['local', 'plugin.py', 'consts.py', 'humblegame.py', 'humbledownloader.py', 'webservice.py']
        modules_full_path = [str(Path(mypy_target) / mod) for mod in modules]
        print(f'running mypy check for {str(Path(mypy_target))} directory')
        c.run("mypy " + ' '.join(modules_full_path) + " --follow-imports silent")
        print('done')


@task
def release(c):
    # TODO: increment version;
    zip_name = f'humblebundle_{__version__}'
    wd = Path(__file__).parent
    tmp_build_dir = wd / zip_name

    arch = wd / (zip_name + '.zip')
    if arch.exists():
        if input(f'{str(arch)} already exists. Proceed? y/n') !='y':
            return

    c.run(f"inv build -o {str(tmp_build_dir)}")
    shutil.make_archive(zip_name, 'zip', root_dir=wd, base_dir=zip_name)
    shutil.rmtree(tmp_build_dir)

    # TODO: publish on github
    # tag = 'v' + __version__
    # print('creating and pushing to origin tag: ', tag)
    # c.run(f'git tag {tag}')
    # c.run(f'git push origin {tag}')
