from galaxy.api.types import Game, LicenseType, LicenseInfo


class HumbleGame:
    def __init__(self, data):
        for k, v in data.items():
            setattr(self, k, v)

    def in_galaxy_format(self):
        licence = LicenseInfo(LicenseType.SinglePurchase)
        dlcs = []  # not supported for now
        return Game(self.machine_name, self.human_name, dlcs, licence)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"HumbleGame({self.human_name}, {self.downloads})"

