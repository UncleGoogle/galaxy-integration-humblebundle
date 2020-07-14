import sys
import time
import psutil
import json
import os
import subprocess
import shutil
from pathlib import Path
from fog.buildtools import buildtools

from invoke import task
import github
from galaxy.tools import zip_folder_to_file


with open('src/manifest.json') as f:
    __version__ = json.load(f)['version']


REQUIREMENTS = 'requirements.txt'
REQUIREMENTS_DEV = 'requirements-dev'
CURRENT_VERSION_FILE = 'current_version.json'

GALAXY_PATH = ''
DIST_DIR = ''
GALAXY_PYTHONPATH = ''

if sys.platform == 'win32':
    PLATFORM = 'Windows'
    GALAXY_PATH = 'C:\\Program Files (x86)\\GOG Galaxy\\GalaxyClient.exe'
    DIST_DIR = os.environ['localappdata'] + '\\GOG.com\\Galaxy\\plugins\\installed'
    PYTHON = 'python'
    GALAXY_PYTHONPATH = str(Path(os.path.expandvars("%programfiles(x86)%")) / "GOG Galaxy" / "python" / "python.exe")
elif sys.platform == 'darwin':
    PLATFORM = 'Mac'
    GALAXY_PATH = "/Applications/GOG Galaxy.app/Contents/MacOS/GOG Galaxy"
    DIST_DIR = os.environ['HOME'] + r"/Library/Application\ Support/GOG.com/Galaxy/plugins/installed"
    PYTHON = 'python3'

DIST_PLUGIN = os.path.join(DIST_DIR, 'humblebundle')
THIRD_PARTY_RELATIVE_DEST = 'modules'



def get_repo():
    token = os.environ['GITHUB_TOKEN']
    g = github.Github(token)
    return g.get_repo('UncleGoogle/galaxy-integration-humblebundle')


def asset_name(tag, platform):
    return f'humble_{tag}_{platform[:3].lower()}.zip'


@task
def install(c, dev=False):
    req = REQUIREMENTS_DEV if dev else REQUIREMENTS
    c.run(f"{PYTHON} -m pip install -r {req}")


@task
def build(c, output='build'):
    print(f'Preparing build to `{output}`')
    buildtools.build(output=output, third_party_output='modules', requirements=REQUIREMENTS)


@task
def dist(c, output=DIST_PLUGIN, galaxy_path=GALAXY_PATH, no_deps=False):
    for proc in psutil.process_iter(attrs=['exe'], ad_value=''):
        if proc.info['exe'] == galaxy_path:
            print(f'Galaxy at {galaxy_path} is running!. Terminating...')
            proc.terminate()
            break
    else:
        print('Galaxy instance not found.')

    if no_deps:
        c.run(f'inv copy -o {output}')
    else:
        c.run(f'inv build -o {output}')

    print(f'Reopening Galaxy from {galaxy_path}')
    subprocess.Popen([galaxy_path])


@task
def debug(c, output=DIST_PLUGIN, deps=False):
    this_plugin = 'plugin-humble'
    for proc in psutil.process_iter(attrs=['exe'], ad_value=''):
        if proc.info['exe'] == GALAXY_PYTHONPATH:
            if this_plugin in proc.cmdline()[-1]:
                print(f'Running plugin instance found!. Terminating...')
                proc.terminate()
                break
    if not deps:
        c.run(f'inv copy -o {output}')
    else:
        c.run(f'inv build -o {output}')
    print("Now, click 'retry' for crashed plugin in Settings")


def recursive_overwrite(src, dest):
    if os.path.isdir(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        files = os.listdir(src)
        for f in files:
            recursive_overwrite(
                os.path.join(src, f),
                os.path.join(dest, f)
            )
    else:
        shutil.copyfile(src, dest)

@task
def copy(c, output=DIST_PLUGIN):
    print('copying source code ...')
    recursive_overwrite('src', output)


@task
def test(c, target=None):
    print(f'Running tests vs code dumped in folder `{target}`')

    if target is not None:
        config = str(Path(__file__).parent / 'pytest-build.ini')
        with open(config, 'w') as f:
            f.write("[pytest]\n")
            f.write(f"python_paths = {target}")  # pytest-pythonpaths required
    else:
        config = 'pytest.ini'

    c.run(f"{PYTHON} -m pytest -c {config} -vv tests/common src --color=yes")
    if sys.platform == 'win32':
        c.run(f"{PYTHON} -m pytest tests/windows")

    if target:
        modules = ['local', 'model', 'plugin.py', 'consts.py', 'humbledownloader.py', 'webservice.py', 'settings.py', 'library.py']
        os.environ['MYPYPATH'] = str(Path(target) / THIRD_PARTY_RELATIVE_DEST)
        modules_full_path = [str(Path(target) / mod) for mod in modules]
        print(f'running mypy check for {str(Path(target))} directory')
        c.run(f"{PYTHON} -m mypy {' '.join(modules_full_path)} --follow-imports silent")
        print('done')


@task
def archive(c, zip_name=None, target=None):
    if target is None:
        build(c, 'build')
        target = 'build'
    if zip_name is None:
        zip_name = f'humblebundle_{__version__}.zip'
    print(f'Zipping build from `{target}` to `{zip_name}`')

    zip_folder_to_file(target, zip_name)
    zip_path = Path('.') / zip_name
    return str(zip_path.resolve())


@task
def curr_ver(c, tag=None):
    """Refresh CURRENT_VERSION_FILE"""
    if tag is None:
        tag = get_repo().get_latest_release().tag_name
    content = {
        "tag_name": tag,
        "assets": []
    }
    for platform in ["Windows", "Mac"]:
        name = asset_name(tag, platform)
        content['assets'].append({
            "browser_download_url": f"https://github.com/UncleGoogle/galaxy-integration-humblebundle/releases/download/{tag}/{name}",
            "name": name
        })
    with open(CURRENT_VERSION_FILE, 'w') as f:
        json.dump(content, f, indent=4)


@task(aliases=['tag'])
def create_tag(c, tag=None):
    if tag is None:
        tag = 'v' + __version__
    branch = c.run("git rev-parse --abbrev-ref HEAD").stdout.strip()

    print(f'New tag version will be: [{tag}] on [{branch}] branch. Is it OK? (make sure new version is committed)')
    if input('y/n').lower() != 'y':
        return

    print(f'Creating and pushing a new tag `{tag}`.')
    c.run(f'git tag {tag}')
    c.run(f'git push origin {tag}')

    print(f'Refreshing {CURRENT_VERSION_FILE}. Push it to master after release')
    curr_ver(c, tag)


@task
def release(c, automa=False):
    tag = 'v' + __version__
    if automa:
        print(f'Creating/updating release with assets for {PLATFORM} to version {tag}')
    else:
        print(f'New tag version for release will be: {tag}. is it OK?')
        if input('y/n').lower() != 'y':
            return

    repo = get_repo()

    for release in repo.get_releases():
        if release.tag_name == tag and release.draft:
            draft_release = release
            break
    else:
        print('No draft release with given tag found.')
        if not automa:
            create_tag(c, tag)

        print(f'Creating new release for tag `{tag}`')
        draft_release = repo.create_git_release(
            tag=tag,
            name=__version__,
            message="draft",
            draft=True,
            prerelease=not automa
        )

    build(c, output='build')
    test(c, target='build')
    asset_path = archive(c, target='build', zip_name=asset_name(tag, PLATFORM))

    print(f'Uploading asset for {PLATFORM}: {asset_path}')
    draft_release.upload_asset(asset_path)
