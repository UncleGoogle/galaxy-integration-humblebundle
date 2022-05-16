"""Component test for the whole authenticationbehavior between Humble API and Galaxy
"""

import pytest
from galaxy.api.errors import AuthenticationRequired


@pytest.mark.asyncio
async def test_authenticaiton_required_401(plugin_with_api, aioresponse):
    url = "https://www.humblebundle.com/api/v1/user/order"
    aioresponse.get(url, status=401)
    cookie = {"name": "simpleauth_session", "value":"123"}
    with pytest.raises(AuthenticationRequired):
        await plugin_with_api.authenticate(cookie)

