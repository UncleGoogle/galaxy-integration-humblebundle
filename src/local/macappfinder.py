import os
import plistlib
import logging
from typing import Optional, Set, Dict
import pathlib
from dataclasses import dataclass

from local.baseappfinder import BaseAppFinder


@dataclass
class BundleInfo:
    location: pathlib.Path
    exe_name: str
    name: str

    @property
    def executable(self) -> pathlib.Path:
        return self.location / 'Contents' / 'MacOS' / self.exe_name


class MacAppFinder(BaseAppFinder):
    DEFAULT_PATH = '/Applications'

    async def __call__(self, owned_title_id, paths=None):
        if paths is None:
            return dict()
        if paths == set():
            paths = {pathlib.Path(self.DEFAULT_PATH)}
        return await super().__call__(owned_title_id, paths)

    def __get_close_matches(dir_name, candidates, similarity):
        """Cuts .app suffix"""
        dir_name_stem = dir_name[:-4] if dir_name.endswith('.app') else dir_name
        return super().get_close_matches(dir_name_stem, candidates, similarity)

    def __find_best_exe(self, dir_path: pathlib.PurePath, app_name: str):
        if dir_path.suffix == '.app':
            return self.__parse_bundle(dir_path)
        return super().__find_best_exe(dir_path, app_name)

    @staticmethod
    def __parse_bundle(app_dir: os.PathLike) -> Optional[pathlib.Path]:
        dir_ = pathlib.Path(app_dir).resolve()
        try:
            with open(dir_ / 'Contents' / 'Info.plist', 'rb') as f:
                plist = plistlib.load(f)  # type: ignore
        except (FileExistsError, OSError) as e:
            logging.error(f'{repr(e)}')
            return None
        try:
            exe_name = plist['CFBundleExecutable']
        except KeyError as e:
            logging.error(f'No Executable in Info.plist: {repr(e)}')
            return None
        try:
            name = plist.get('CFBundleDisplayName', plist['CFBundleName'])
        except KeyError:
            name = pathlib.PurePath(app_dir).stem
        bundle = BundleInfo(dir_, exe_name, name)
        return bundle.executable
    