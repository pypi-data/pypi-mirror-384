import pytest

from src.battlenet_client.utils.constants import VALID_REGIONS
from src.battlenet_client.api.oauth import user_info, token_validation
from src.battlenet_client.utils.exceptions import BNetRegionNotFoundError

from tests.constants import INVALID_REGIONS


@pytest.mark.parametrize('region_tag', VALID_REGIONS)
def test_user_info(region_tag):
    token = 'my_good_token_1234'
    data = user_info(region_tag, token)
    assert isinstance(data, tuple)
    assert isinstance(data[0], str)
    if region_tag == 'cn':
        assert data[0] == "https://oauth.battlenet.com.cn/userinfo"
    else:
        assert data[0] == f'https://oauth.battle.net/userinfo'



@pytest.mark.parametrize('region_tag', INVALID_REGIONS)
def test_user_info_invalid_region(region_tag):
    with pytest.raises(BNetRegionNotFoundError):
        user_info(region_tag)


@pytest.mark.parametrize('region_tag', VALID_REGIONS)
def test_token_validation(region_tag):
    token = 'my_good_token_1234'
    data = token_validation(region_tag, token)
    assert isinstance(data, tuple)
    assert isinstance(data[0], str)
    if region_tag == 'cn':
        assert data[0] == "https://oauth.battlenet.com.cn/check_token"
    else:
        assert data[0] == 'https://oauth.battle.net/check_token'
    assert data[1] is None
    assert isinstance(data[2], dict)
    assert 'token' in data[2].keys()
    assert token == data[2]["token"]
    assert data[3] is None


@pytest.mark.parametrize('region_tag', INVALID_REGIONS)
def test_token_validation_invalid_region(region_tag):
    with pytest.raises(BNetRegionNotFoundError):
        token = 'my_good_token_1234'
        token_validation(region_tag, token)
