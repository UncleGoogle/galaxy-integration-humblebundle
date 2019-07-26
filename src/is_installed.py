import dataclasses
import typing
from consts import CURRENT_SYSTEM, HP, WINDOWS_UNINSTALL_LOCATION

if CURRENT_SYSTEM == HP.WINDOWS:
    import winreg


def is_app_installed(app_name):
    if CURRENT_SYSTEM == HP.WINDOWS:
        return _is_installed_windows(app_name)
    else:
        raise NotImplementedError


@dataclass
class UninstallKey:
    key_name: str
    display_name: str
    uninstall_cmd: str
    install_location: Optional[str]
    path: Optional[str]


# all_installed = RegistryHive.LocalMachine + RegistryHive.CurrentUser


class WindowsClient:
    def __init__(self):
        self._uninstall_entries = {}  # Dict[str<display_name>, UninstallKey]
        self.refresh()

    def refresh(self):
        reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        with winreg.OpenKey(reg, WINDOWS_UNINSTALL_LOCATION) as key:
            subkeys = winreg.QueryInfoKey(key)[0]
            for i in range(subkeys):
                subkey_name = winreg.EnumKey(key, i)
                with winreg.OpenKey(key, subkey_name) as subkey:
                    display_name = winreg.QueryValue(subkey, 'DisplayName')
                    self._uninstall_entries =

                    if product in winreg.QueryValue(subkey, 'DisplayName') or product.replace(':', '') in winreg.QueryValueEx(subkey, 'DisplayName'):
                        if 'bethesdanet://uninstall' in winreg.QueryValueEx(subkey, 'UninstallString')[0]:

    def _parse_uninstall_entry(self, subkey):
        return UninstallKey(
            key_name =
            display_name = winreg.QueryValue(subkey, 'DisplayName')
            uninstall_cmd = winreg.QueryValue(subkey, 'UninstallString')
            # install_location: Optional[str]
            # path: Optional[str]
        )


# def _is_installed_windows(self, local_game):
#     try:
#         reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
#         with winreg.OpenKey(reg, WINDOWS_UNINSTALL_LOCATION) as key:
#             winreg.OpenKey(key, local_game['registry_path'])
#             if os.path.exists(local_game['path']):
#                 return True
#     except OSError:
#         return False

    def get_installed_games(self, products):
        installed_games = {}
        products_to_scan = products.copy()

        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            with winreg.OpenKey(reg, WINDOWS_UNINSTALL_LOCATION) as key:

                # Do a quicker, easier exclude for items which are already in the cache
                for product in products_to_scan.copy():
                    if product in self.local_games_cache:
                        try:
                            winreg.OpenKey(key, self.local_games_cache[product]['registry_path'])
                            if os.path.exists(self.local_games_cache[product]['path']):
                                installed_games[product] = self.local_games_cache[product]['local_id']
                            products_to_scan.pop(product)
                        except OSError:
                            products_to_scan.pop(product)
                log.info("Scanned through local games cache")
                for i in range(0, winreg.QueryInfoKey(key)[0]):
                    subkey_name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, subkey_name) as subkey:
                        # Try to find installed products retrieved by api requests,
                        # use copy because the dict can be modified by other methods since this is an async check
                        for product in products_to_scan.copy():
                            try:
                                try:
                                    winreg.QueryValueEx(subkey, 'DisplayName')[0]
                                except:
                                    continue
                                if product in winreg.QueryValueEx(subkey, 'DisplayName')[0] or product.replace(':', '') in winreg.QueryValueEx(subkey, 'DisplayName')[0]:
                                    if 'bethesdanet://uninstall' in winreg.QueryValueEx(subkey, 'UninstallString')[0]:
                                        unstring = winreg.QueryValueEx(subkey, "UninstallString")[0]
                                        local_id = unstring.split('bethesdanet://uninstall/')[1]
                                        path = winreg.QueryValueEx(subkey, "Path")[0]

                                        self.local_games_cache[product] = {'local_id': local_id,
                                                                        'registry_path': subkey_name,
                                                                        'path': path.strip('\"')}
                                        installed_games[product] = local_id
                            except OSError as e:
                                log.info(f"Encountered OsError while parsing through registry keys {repr(e)}")
                                continue
        except OSError:
            log.error(f"Unable to parse registry for installed games")
            return installed_games
        except Exception:
            log.exception(f"Unexpected error when parsing registry")
            raise
        log.info(f"Returning {installed_games}")
        return installed_games
