from local.baseappfinder import BaseAppFinder


class MacAppFinder(BaseAppFinder):
    async def find_local_games(self, owned_title_id, paths):
        if paths:
            return await super().find_local_games(owned_title_id, paths)
        return []
