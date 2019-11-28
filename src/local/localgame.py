import dataclasses
import subprocess
import pathlib
import psutil
from typing import Optional

from galaxy.api.types import LocalGameState, LocalGame

from consts import IS_WINDOWS

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

    def run(self):
        # flags = 0b0001000  # DETACHED_PROCESS on Windows
        proc = subprocess.Popen(str(self.executable), cwd=self.executable.parent, creationflags=flags)
        self.process = psutil.Process(proc.pid)

    def uninstall(self):
        subprocess.Popen(self.uninstall_cmd)
