import pytest

from galaxy.unittest.mock import skip_loop


@pytest.mark.asyncio
async def test_humbleapp_refresh_game_list(plugin, humbleapp_client_mock):
    plugin.tick()
    await skip_loop()
    humbleapp_client_mock.refresh_game_list.assert_called_once()
