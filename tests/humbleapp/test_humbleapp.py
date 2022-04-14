from functools import partial
import pathlib
import sys
from unittest.mock import Mock, patch
from humbleapp.humbleapp import FileWatcher, GameMachineName, GameStatus, HumbleAppClient, VaultGame, parse_humble_app_config

import pytest


class TestFileWatcher:
    @pytest.fixture
    def watched_file(self, tmp_path: pathlib.Path) -> FileWatcher:
        file_ = tmp_path / 'config.json'
        file_.touch()
        return FileWatcher(file_)

    @pytest.fixture
    def checked_file(self, watched_file: FileWatcher) -> FileWatcher:
        watched_file.has_changed()
        return watched_file

    def test_first_check_is_treated_as_changed(self, watched_file):
        assert watched_file.has_changed() == True
    
    def test_subsequent_check_says_not_changed(self, checked_file):
        assert checked_file.has_changed() == False

    def test_check_after_modification_says_file_changed(self, checked_file):
        with open(checked_file.path, 'w') as f:
            f.write('xxx')
        assert checked_file.has_changed() == True

    def test_check_changed_file_when_is_still_open_sayd_file_changed(self, checked_file):
        with open(checked_file.path, 'w') as f:
            f.write('xxx')
            assert checked_file.has_changed() == True

    def test_check_after_read_says_file_changed(self, checked_file):
        with open(checked_file.path, 'r') as f:
            f.read()
        assert checked_file.has_changed() == False
    
    def test_file_no_longer_not_exists(self, checked_file):
        checked_file.path.unlink()
        assert checked_file.has_changed() == None

    def test_file_started_to_exists(self, watched_file):
        watched_file.path.unlink()
        watched_file.has_changed()
        watched_file.path.touch()
        assert watched_file.has_changed() == True


class TestHumbleAppConfigParser():
    @pytest.fixture(autouse=True)
    def setup(self, config_path):
        self.parser = parse_humble_app_config
        self.parse = partial(self.parser, config_path)
    
    @pytest.fixture(scope="class")
    def config_path(self) -> pathlib.Path:
        return pathlib.Path(__file__).parents[1] / "data" / "humble_app_config.json"
    
    def test_settings(self):
        result = self.parse()
        s = result.settings
        assert s.download_location == pathlib.Path("C:/Games/Humbleapp")

    def test_parse_installed_game(self):
        result = self.parse()
        assert len(result.game_collection) > 0
        for g in result.game_collection:
            if g.machine_name == 'forager_collection':
                break
        assert isinstance(g, VaultGame)
        assert g.game_name == 'Forager'
        assert g.status == GameStatus.INSTALLED
        assert g.is_available == True
        assert g.last_played == 1648036757
        assert g.file_size == 144845035
        assert g.full_executable_path == pathlib.Path("C:/Games/Humbleapp/forager_windows/forager.exe") 
        assert g.date_added == 1643738400
        assert g.date_ended == None


class TestHumbleAppClient:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = HumbleAppClient()

    @pytest.mark.skipif(sys.platform != 'win32', reason="not windows")
    def test_get_exe_path(self):
        cmd_template = R'"c:\Users\AUser\AppData\Local\Programs\Humble App\Humble App.exe" "%1"'
        with patch("winreg.OpenKey"), patch("winreg.QueryValue", return_value=cmd_template):
            assert self.client.get_exe_path() == R"c:\Users\AUser\AppData\Local\Programs\Humble App\Humble App.exe"
            
    def test_is_installed_no_exe_path_found(self):
        with patch.object(self.client, "get_exe_path", Mock(return_value=None)):
            assert self.client.is_installed() == False

    @pytest.mark.parametrize("exe_exists", [True, False])
    def test_is_installed_exe_path_found(self, tmp_path: pathlib.Path, exe_exists: bool):
        path = tmp_path / "Humble App.exe"
        if exe_exists:
            path.touch()
        with patch.object(self.client, "get_exe_path", Mock(return_value=path)):
            assert self.client.is_installed() == exe_exists
    
    @pytest.mark.parametrize("method", ["launch", "download", "uninstall"])
    def test_command_handler(self, method: str):
        game_id = GameMachineName("game_machine_name")
        with patch("webbrowser.open") as m:
            getattr(self.client, method)(game_id)
            m.assert_called_once_with(f"humble://{method}/{game_id}")
