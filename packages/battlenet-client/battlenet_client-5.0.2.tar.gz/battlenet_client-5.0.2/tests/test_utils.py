import pytest
from src.battlenet_client.utils import utils
from src.battlenet_client.utils.exceptions import BNetValueError


@pytest.mark.parametrize(
    "value",
    [(1723, 40, 32), [1723, 40, 32], {"gold": 1723, "silver": 40, "copper": 32}],
)
def test_currency_convertor_invalid_type(value):
    with pytest.raises(BNetValueError):
        utils.currency_convertor(value)


def test_currency_convertor_negative_number():
    with pytest.raises(BNetValueError):
        utils.currency_convertor(-43_23_11)


@pytest.mark.parametrize("value", ["17234032"])
def test_currency_convertor_str(value):
    with pytest.raises(BNetValueError):
        utils.currency_convertor(value)


def test_slugify_with_int():
    result = utils.slugify(81)
    assert isinstance(result, str)
    assert result == "81"


def test_slugify_with_tuple():
    with pytest.raises(AttributeError):
        # noinspection PyTypeChecker
        utils.slugify((1, 3, 4))


def test_slugify_with_str():
    result = utils.slugify("We'll Be Back")
    assert isinstance(result, str)
    assert result == 'well-be-back'


def test_localize_with_none():
    result = utils.localize(None)
    assert result is None


def test_localize_with_int():
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        result = utils.localize(81)


def test_localize_with_aaus():
    with pytest.raises(BNetValueError):
        utils.localize('aaUS')


def test_localize_with_enaa():
    with pytest.raises(BNetValueError):
        utils.localize('enaa')


def test_localize_with_enus():
    result = utils.localize('enUS')
    assert isinstance(result, str)
    assert result == 'en_US'


def test_api_host_cn():
    result = utils.api_host('CN')
    assert result == "https://gateway.battlenet.com.cn"


def test_api_host_us():
    result = utils.api_host('US')
    assert result == "https://us.api.blizzard.com"


def test_auth_host_cn():
    result = utils.auth_host('CN')
    assert result == "https://oauth.battlenet.com.cn"


def test_auth_host_us():
    result = utils.auth_host('US')
    assert result == 'https://oauth.battle.net'
