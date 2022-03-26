from functools import partial
import pathlib
from humbleapp import FileWatcher, GameStatus, VaultGame, parse_humble_app_config

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
        with pytest.raises(FileNotFoundError):
            checked_file.has_changed()


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
        g = result.game_collection['forager_collection']
        assert isinstance(g, VaultGame)
        assert g.machine_name == 'forager_collection'
        assert g.game_name == 'Forager'
        assert g.status == GameStatus.INSTALLED
        assert g.is_available == True
        assert g.last_played == 1648036757
        assert g.file_size == 144845035
        assert g.full_executable_path == pathlib.Path("C:/Games/Humbleapp/forager_windows/forager.exe") 
        assert g.date_added == 1643738400
        assert g.date_ended == None