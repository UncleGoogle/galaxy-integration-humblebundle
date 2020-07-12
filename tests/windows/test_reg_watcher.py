import os
import pytest
import pathlib
from unittest.mock import patch
from contextlib import contextmanager

try:
    from local.winappfinder import WindowsAppFinder
    from local.reg_watcher import WinRegUninstallWatcher, UninstallKey
except ModuleNotFoundError:
    pass # workaround vscode discovery test problems


@pytest.fixture
def patch_wrc():
    @contextmanager
    def fn(subkeys):
        def mock_get_val(subkey, prop, optional=False):
            if optional:
                return subkey.get(prop)
            return subkey[prop]

        with patch.object(WinRegUninstallWatcher, "_iterate_new_uninstall_keys") as subkey_gen, \
             patch.object(WinRegUninstallWatcher, "_WinRegUninstallWatcher__get_value") as get_val:
            subkey_gen.return_value = iter(subkeys)
            get_val.side_effect = mock_get_val
            yield
    return fn


@pytest.fixture
def uk_annas_quest():
    return UninstallKey(
        key_name="Anna's Quest_is1",
        display_name="Anna's Quest",
        uninstall_string="\"D:\\Games\\Anna's Quest\\unins000.exe\"",
        install_location="D:\\Games\\Anna's Quest\\",
    )


@pytest.fixture
def uk_windosill():
    return UninstallKey(
        key_name="Windosill_is1",
        display_name= "Windosill version 1.61",
        uninstall_string="\"C:\\Games\\The Windosill\\uninstall.exe\"",
        install_location="C:\\Games\\The Windosill\\"
    )


# ---------- UninstallKey -----------

def test_uk_display_icon_path():
    display_icons = ["\"C:\\abc\\s.ico\",0", "C:\\abc\\s.ico,1", "C:\\abc\\s.ico", "\"C:\\abc\\s.ico\""]
    for i in display_icons:
        uk = UninstallKey('', '', '', display_icon=i)
        assert pathlib.Path("C:\\abc\\s.ico") == uk.display_icon_path


@pytest.mark.parametrize('uninstall_string', [
    R'D:\Games\HoMM 3 Complete\unins000.exe',
    R'"D:\Games\HoMM 3 Complete\unins000.exe"',
    R'"D:\Games\HoMM 3 Complete\unins000.exe" /SILENT',
    R'"D:\Games\HoMM 3 Complete\unins000.exe" uninstall extra_path "C:\ProgramData\HoMM\saves"',
    R'"D:\Games\HoMM 3 Complete\unins000.exe" --lang=esMX --display-name="Heroes 3"'
])
def test_uk_local_uninstaller_path(uninstall_string):
    expected = pathlib.Path(R"D:\Games\HoMM 3 Complete\unins000.exe")
    uk = UninstallKey('', '', uninstall_string=uninstall_string)
    assert expected == uk.local_uninstaller_path


def test_uk_local_uninstaller_path_empty():
    assert None == UninstallKey('', '', uninstall_string='').local_uninstaller_path


def test_uk_local_uninstaller_path_msi():
    """No support for msi uninstallers for now"""
    uninstall_string = 'MsiExec.exe /I{20888FA1-8127-42E3-969F-9BF93245AC83}'
    uk = UninstallKey('', '', uninstall_string=uninstall_string)
    assert None == uk.local_uninstaller_path


@pytest.mark.parametrize('uninstall_string', [
    R'"C:\WINDOWS\iun504.exe" "C:\Program Files (x86)\Blades of Avernum"',
])
def test_uk_local_uninstaller_path_other_uninstallers(mocker, uninstall_string):
    """Should ignore uninstalers from system locations"""
    mocker.patch.dict(os.environ,  {"WINDIR": R"C:\WINDOWS"})
    uk = UninstallKey('', '', uninstall_string=uninstall_string)
    assert None == uk.local_uninstaller_path


# --------- WinRegClient ---------------

def test_refresh_uks(uk_annas_quest, uk_windosill, patch_wrc):
    subkeys = [
        ("Anna's Quest_is1", {
        "DisplayName": "Anna's Quest",
        "InstallLocation": "D:\\Games\\Anna's Quest\\",
        "UninstallString": "\"D:\\Games\\Anna's Quest\\unins000.exe\""
        }),
        (uk_windosill.key_name, {
            "DisplayName": uk_windosill.display_name,
            "InstallLocation": uk_windosill.install_location,
            "UninstallString": uk_windosill.uninstall_string
        })
    ]
    expected = set([uk_annas_quest, uk_windosill])
    with patch_wrc(subkeys):
        finder = WindowsAppFinder()
        finder._reg.refresh()
        assert finder._reg.uninstall_keys == expected
