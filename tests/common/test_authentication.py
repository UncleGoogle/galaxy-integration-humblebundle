"""Component test for the whole authenticationbehavior between Humble API and Galaxy
"""

import pytest
from galaxy.api.errors import AuthenticationRequired


@pytest.fixture()
def user_id():
    return 5896125009870848


@pytest.fixture
def auth_cookie():
    """In the form returned from Galaxy buildin browser to the plugin; user_id encoded inside"""
    return {
        "name": "simpleauth_session",
        "value":"eyJ1c2VyX2lkIjo1ODk2MTI1MDA5ODcwODQ4LCJpZCI6IldmR0VWa2FBTzYiLCJyZWZlcnJlcl9jb2RlIjoiIiwiYXV0aF90aW1lIjoxNTg4OTcxNjUxfQ==|1597686340|471b70236a3d9ea0c8499563187a3609a7459087;"
    } 


@pytest.mark.asyncio
async def test_authentication_401(plugin_with_api, aioresponse, auth_cookie):
    url = "https://www.humblebundle.com/api/v1/user/order"
    aioresponse.get(url, status=401)
    with pytest.raises(AuthenticationRequired):
        await plugin_with_api.authenticate(auth_cookie)


@pytest.fixture
def fetching_user_email(aioresponse):
    """Dummy mock""" 
    aioresponse.get("https://www.humblebundle.com/", status=200)


@pytest.mark.asyncio
@pytest.mark.usefixtures('fetching_user_email')
async def test_authenticaiton_200(plugin_with_api, aioresponse, auth_cookie, user_id):
    url = "https://www.humblebundle.com/api/v1/user/order"
    aioresponse.get(url, status=200, payload=[{'gamekey': 'WdxNUbxE4MZqSb1F'}, {'gamekey': '6CMnzBDP46e4a28d'}])
    response = await plugin_with_api.authenticate(auth_cookie)
    assert response.user_id == user_id
