import pytest
from src.battlenet_client.client import BattlenetClient
from decouple import config


def test_battlenet_client_client_credentials():
    client = BattlenetClient.client_credential("us", config("CLIENT_ID"), config("CLIENT_SECRET"))
    assert client.client_id == config("CLIENT_ID")
    assert client.client_secret == config("CLIENT_SECRET")
    assert client.region == "us"
    assert client.oauth.access_token is not None
    assert client.oauth.token is not None
    assert isinstance(client.oauth.access_token, str)
    assert isinstance(client.oauth.token, dict)
    assert client.oauth.token["token_type"] == "bearer"
    assert client.oauth.token["expires_in"] == 86399
    assert client.oauth.token["sub"] == config("CLIENT_ID")

def test_battlenet_client_client_credentials_failed_region():
    client = BattlenetClient.client_credential("zz", config("CLIENT_ID"), config("CLIENT_SECRET"))
    assert client.client_id == config("CLIENT_ID")
    assert client.client_secret == config("CLIENT_SECRET")
    assert client.region != "us"
    assert client.oauth.access_token is not None
    assert client.oauth.token is not None
    assert isinstance(client.oauth.access_token, str)
    assert isinstance(client.oauth.token, dict)
    assert client.oauth.token["token_type"] == "bearer"
    assert client.oauth.token["expires_in"] == 86399
    assert client.oauth.token["sub"] == config("CLIENT_ID")