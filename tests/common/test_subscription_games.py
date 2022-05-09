from unittest.mock import Mock
import pytest

from conftest import AsyncMock

from galaxy.api.types import SubscriptionGame
from galaxy.api.errors import UnknownError
from local.humbleapp_adapter import HumbleAppGameCategory
from model.game import TroveGame, ChoiceGame
from model.subscription import ChoiceContentData, ContentChoiceOptions
from consts import TROVE_SUBSCRIPTION_NAME


@pytest.mark.asyncio
async def test_trove(plugin):
    ctx = None
    with pytest.raises(UnknownError):
        async for _ in plugin.get_subscription_games(TROVE_SUBSCRIPTION_NAME, ctx):
            pass


@pytest.mark.asyncio
async def test_trove_load_from_persistent_cache(plugin):
    plugin.persistent_cache['trove_games'] = '[' \
        '{"human-name": "A", "machine_name": "a", "downloads": {"windows": {}}}, ' \
        '{"human-name": "C", "machine_name": "c", "downloads": {"mac": {}}}' \
    ']'
    plugin.handshake_complete()
    assert plugin._trove_games == {
        'a': TroveGame({'human-name': 'A', 'machine_name': 'a', 'downloads': {'windows': {}}}),
        'c': TroveGame({'human-name': 'C', 'machine_name': 'c', 'downloads': {'mac': {}}}),
    }


@pytest.fixture
def cco():
    return Mock(spec=ContentChoiceOptions, name='cco')


@pytest.fixture
def choice_data(cco):
    mock = Mock(spec=ChoiceContentData)
    mock.content_choice_options = cco
    return mock


@pytest.mark.asyncio
@pytest.mark.parametrize("remaining_choices", [
    pytest.param(None, id="choices unlimited or unaplicable"),
    pytest.param(5, id="some remaining choices left"),
])
async def test_humble_monthly_v2_sufficient_condition_to_show_all_games(
    api_mock,
    plugin,
    cco,
    choice_data,
    remaining_choices,
):
    """Show all possible games to be aquired in case there is no choice limit."""
    cco.remaining_choices = remaining_choices
    cco.content_choices_made = ['c']
    cco.content_choices = [
        Mock(**{'id': 'a', 'title': 'A'}),
        Mock(**{'id': 'b', 'title': 'B'}),
        Mock(**{'id': 'c', 'title': 'C'}),
    ]
    cco.extrases = [
        Mock(**{'machine_name':'e', 'human_name': 'E'})
    ]
    api_mock.get_choice_content_data = AsyncMock(return_value=choice_data)
    ctx = None
    async for one_month_games in plugin.get_subscription_games('Humble Choice 2020-05', ctx):
        assert one_month_games == [
            SubscriptionGame(game_title='A', game_id='a'),
            SubscriptionGame(game_title='B', game_id='b'),
            SubscriptionGame(game_title='C', game_id='c'),
            SubscriptionGame(game_title='E', game_id='e'),
        ]
    assert plugin._choice_games == {  # cache
        'a': ChoiceGame(id='a', title='A', slug='may-2020', is_extras=False),
        'b': ChoiceGame(id='b', title='B', slug='may-2020', is_extras=False),
        'c': ChoiceGame(id='c', title='C', slug='may-2020', is_extras=False),
        'e': ChoiceGame(id='e', title='E', slug='may-2020', is_extras=True),
    }


@pytest.mark.asyncio
async def test_choice_month_no_remaining_choices(api_mock, plugin, cco, choice_data):
    """Show only chosen games if no more choices left."""
    cco.remaining_choices = 0
    cco.content_choices_made = ['c']
    cco.content_choices = [
        Mock(**{'id': 'a', 'title': 'A'}),
        Mock(**{'id': 'b', 'title': 'B'}),
        Mock(**{'id': 'c', 'title': 'C'}),
    ]
    cco.extrases = [
        Mock(**{'machine_name':'e', 'human_name': 'E'})
    ]
    api_mock.get_choice_content_data = AsyncMock(return_value=choice_data)
    ctx = None
    async for one_month_games in plugin.get_subscription_games('Humble Choice 2020-05', ctx):
        assert one_month_games == [
            SubscriptionGame(game_title='C', game_id='c'),
            SubscriptionGame(game_title='E', game_id='e'),
        ]
    assert plugin._choice_games == {  # cache
        'c': ChoiceGame(id='c', title='C', slug='may-2020', is_extras=False),
        'e': ChoiceGame(id='e', title='E', slug='may-2020', is_extras=True),
    }


@pytest.mark.asyncio
async def test_choice_store_in_presistent_cache(plugin):
    plugin.push_cache.reset_mock()
    plugin._choice_games = {
        'c': ChoiceGame(id='c', title='C', slug='may-2020', is_extras=False),
        'e': ChoiceGame(id='e', title='E', slug='may-2020', is_extras=True),
    }
    plugin.subscription_games_import_complete()
    assert plugin.persistent_cache['choice_games'] == '[' \
        '{"id": "c", "title": "C", "slug": "may-2020", "is_extras": false}, ' \
        '{"id": "e", "title": "E", "slug": "may-2020", "is_extras": true}' \
    ']'
    plugin.push_cache.assert_called()


@pytest.mark.asyncio
async def test_choice_load_from_persistent_cache(plugin):
    plugin.persistent_cache['choice_games'] = '[' \
        '{"id": "c", "title": "C", "slug": "may-2020", "is_extras": false}, ' \
        '{"id": "e", "title": "E", "slug": "may-2020", "is_extras": true}' \
    ']'
    plugin.handshake_complete()
    assert plugin._choice_games == {
        'c': ChoiceGame(id='c', title='C', slug='may-2020', is_extras=False),
        'e': ChoiceGame(id='e', title='E', slug='may-2020', is_extras=True),
    }

@pytest.mark.asyncio
@pytest.mark.parametrize("category", HumbleAppGameCategory)
async def test_humble_app_games(
    plugin,
    humbleapp_client_mock,
    category,
):
    subscription_name = category.value
    expected = [SubscriptionGame(game_title='A', game_id='a')]

    def fake_get_sub_games(game_cat: HumbleAppGameCategory) :
        if game_cat is category:
            return expected
        return []

    humbleapp_client_mock.get_subscription_games.side_effect = fake_get_sub_games

    ctx = await plugin.prepare_subscription_games_context([subscription_name])
    
    async for games_batch in plugin.get_subscription_games(subscription_name, ctx):
        assert games_batch == expected
    humbleapp_client_mock.refresh_game_list.assert_called_once()