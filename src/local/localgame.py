import dataclasses
import subprocess
import pathlib
import psutil
from typing import Optional

from galaxy.api.types import LocalGameState, LocalGame

from consts import HP, CURRENT_SYSTEM

DETACHED_PROCESS = 0b0001000


@dataclasses.dataclass
class LocalHumbleGame:
    machine_name: str
    executable: pathlib.Path
    uninstall_cmd: Optional[str] = None
    process: Optional[psutil.Process] = None

    @property
    def id(self):
        return self.machine_name

    @property
    def is_installed(self):
        return self.executable.exists()

    @property
    def is_running(self):
        if self.process is None:
            return False
        return self.process.is_running()

    @property
    def state(self):
        state = LocalGameState.None_
        if self.is_installed:
            state = LocalGameState.Installed
        if self.is_running:
            state |= LocalGameState.Running
        return state

    def in_galaxy_format(self):
        return LocalGame(self.machine_name, self.state)
    
    @property
    def bundle_name(self) -> Optional[pathlib.Path]:
        assert CURRENT_SYSTEM == HP.MAC, "macos only property"
        for p in self.executable.parents:
            if p.suffix == '.app':
                return p
        return None

    def run(self):
        if CURRENT_SYSTEM == HP.WINDOWS:
            flags = DETACHED_PROCESS
            proc = subprocess.Popen(str(self.executable), cwd=self.executable.parent, creationflags=flags)
        elif CURRENT_SYSTEM == HP.MAC:
            '''
            -a   Opens with the specified application.
            -W   Blocks until the used applications are closed (even if they were already running).
            '''
            app_name = self.bundle_name or self.executable
            cmd = ["/usr/bin/open", "-W", "-a", str(app_name)]
            proc = subprocess.Popen(cmd, cwd=app_name.parent)

        self.process = psutil.Process(proc.pid)

    def uninstall(self):
        subprocess.Popen(self.uninstall_cmd)
