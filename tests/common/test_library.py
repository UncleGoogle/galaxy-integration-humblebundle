import pytest
from unittest.mock import Mock

from settings import OwnedSettings
from library import LibraryResolver, Strategy
from consts import SOURCE
from model.game import Subproduct, Key, TroveGame


@pytest.fixture
def create_resolver(plugin_mock):
    def fn(settings, cache={}):
        return LibraryResolver(
            api=plugin_mock._api,
            settings=settings,
            cache=cache,
            save_cache_callback=plugin_mock._save_cache
        )
    return fn


def test_library_filters(create_resolver, overgrowth):
    settings = OwnedSettings((SOURCE.DRM_FREE), show_revealed_keys=True)
    resolver = create_resolver(settings)

    resolver._api.get_gamekeys.return_value = [overgrowth['gamekey']]
    resolver._api.order_details.return_value = [overgrowth]
    assert resolver(Strategy.FETCH) == [Subproduct(overgrowth)]


