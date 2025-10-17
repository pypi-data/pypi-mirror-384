from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from collections.abc import Callable
from typing import Optional, Type
from requests import HTTPError
from time import sleep
from urllib.parse import quote_plus

from .cache.base import BaseCache
from .api.oauth import fetch_token, token_validation
from .utils.utils import auth_host, api_host, slugify


class BattlenetClient:
    oauth = None
    state = None
    region = None
    client_id = None
    client_secret = None
    redirect_uri = None
    cache = None
    config_endpoint = None
    jwks = None

    def __init__(self, region: str, oauth: OAuth2Session, cache = Optional[Type[BaseCache]]):
        self.region = region
        self.oauth = oauth
        self.cache = cache
        self.auth_host = auth_host(region)
        self.api_host = api_host(region)

        if self.grant_type == 'client_credentials':
            self.get_token()


    @classmethod
    def client_credential(cls, region: str,  client_id: str, client_secret: str, *,
                          scope: Optional[list[str]] = None, auto_refresh_url: Optional[str] = None,
                          auto_refresh_kwargs: Optional[dict] = None, updater:Optional[Callable]=None,
                          cache = Optional[BaseCache]):
        """ Creates an instance of client credential grant oauth2 session

        Args:
            region (str): The region where the client is connected
            client_id (str): Client ID issued by develop.battle.net
            client_secret (str): Client secret issued by develop.battle.net
            scope (str): The scope of the request
            auto_refresh_url (Optional[str]): Auto-refresh URL when token expires
            auto_refresh_kwargs (Optional[dict]): Extra arguments passed to OAuth2Session for automatic token refresh
            updater (optinal function): specify the function to call when update to the token is required
            cache (instance of `SQLCache` or `NoSQLCache`): cache system

        Returns:
            instance of BattlenetClient configured for client credentials grant oauth2 session
        """
        cls.client_id = client_id
        cls.client_secret = client_secret
        cls.grant_type = 'client_credentials'

        cls.scope = " ".join(scope) if scope else None

        updater = cls.token_updater if updater is None else updater

        if auto_refresh_url and auto_refresh_kwargs:
            oauth = OAuth2Session(client=BackendApplicationClient(client_id=client_id),
                                  auto_refresh_url=auto_refresh_url,
                                  auto_refresh_kwargs=auto_refresh_kwargs,
                                  token_updater=updater)
        else:
            oauth = OAuth2Session(client=BackendApplicationClient(client_id=client_id))

        return cls(region, oauth, cache)

    @classmethod
    def authorization_code(cls, region, client_id: str, client_secret: str, redirect_uri: str, scope: list[str], *,
                           auto_refresh_url: Optional[str] = None, auto_refresh_kwargs: Optional[dict] = None,
                           updater: Callable[[dict], None] = None, cache: Optional[BaseCache] = None):
        """ Creates an instance of authorization code grant oauth2 session

        Args:
            region (str): The region where the client is connected
            client_id (str): Client ID issued by develop.battle.net
            client_secret (str): Client secret issued by develop.battle.net
            redirect_uri (str): URL to send to authorization service to return
            scope (list[str]): list of scopes to grant
            auto_refresh_url (Optional[str]): Auto-refresh URL when token expires
            auto_refresh_kwargs (Optional[dict]): Extra arguments passed to OAuth2Session for automatic token refresh
            updater (callable, optional): the function to perform the automatic update
            cache (instance of `SQLCache` or `NoSQLCache`): cache system

        Returns:
            instance of BattlenetClient configured for authorization code grant oauth2 session
        """
        cls.client_id = quote_plus(client_id)
        cls.client_secret = quote_plus(client_secret)
        cls.scope = ' '.join(scope)

        cls.grant_type = 'authorization_code'

        if "openid" in scope:
            cls.grant_type = 'openid'

        cls.redirect_uri = redirect_uri
        updater = updater if updater else cls.token_updater

        oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope, auto_refresh_url=auto_refresh_url,
                              auto_refresh_kwargs=auto_refresh_kwargs, token_updater=updater)
        return cls(region, oauth, cache)

    @classmethod
    def open_id(cls, region, client_id: str, client_secret: str, redirect_uri: str, scope: list[str], *,
                           auto_refresh_url: Optional[str] = None, auto_refresh_kwargs: Optional[dict] = None,
                           updater: Callable[[dict], None] = None, cache: Optional[BaseCache] = None):
        """ Creates an instance of authorization code grant oauth2 session

        Args:
            region (str): The region where the client is connected
            client_id (str): Client ID issued by develop.battle.net
            client_secret (str): Client secret issued by develop.battle.net
            redirect_uri (str): URL to send to authorization service to return
            scope (list[str]): list of scopes to grant
            auto_refresh_url (Optional[str]): Auto-refresh URL when token expires
            auto_refresh_kwargs (Optional[dict]): Extra arguments passed to OAuth2Session for automatic token refresh
            updater (callable, optional): the function to perform the automatic update
            cache (instance of `SQLCache` or `NoSQLCache`): cache system

        Returns:
            instance of BattlenetClient configured for authorization code grant oauth2 session
        """
        cls.scope = scope.append("openid")
        cls.config_endpoint = f"{auth_host(region)}/.well-known/openid-configuration"
        cls.jwks = f"{auth_host(region)}/jwks/certs"

        return cls.authorization_code(region, client_id, client_secret, redirect_uri, scope,
                                      auto_refresh_url=auto_refresh_url, auto_refresh_kwargs=auto_refresh_kwargs,
                                      updater=updater, cache=cache)

    def get_authorization_url(self) -> str:
        """ Creates an authorization url grant oauth2 URL

        Returns:
          str: authorization url
        """
        url, self.state = self.oauth.authorization_url(f"{auth_host(self.region)}/authorize")
        return url

    def callback(self, code: str, state: str) -> None:
        """ Creates an authorization code grant oauth2 session

        Args:
            code (str): code provided during the callback request
            state (str): state provided by the callback request
        """
        if state == self.state:
            self.get_token(code)

    def token_updater(self, token: dict):
        """ Function to update the token after a refresh

        Args:
            token (dict): token returned from authorization server
        """
        if token:
            self.oauth.token = token
            self.oauth.access_token = token["access_token"]

    def get_token(self, code: Optional[str]=None) -> None:
        """ Fetches the token from the authorization server

        Args
            code (Optional[str]): authorization code provided by authorization server
        """
        url, _, _ = fetch_token(self.region, self.grant_type, self.client_id, redirect_uri=self.redirect_uri, code=code)

        auth = (self.client_id, self.client_secret)

        token = self.oauth.fetch_token(url, auth=auth, code=code)

        self.token_updater(token)

    def check_token(self, *, locale: Optional[str]=None) -> bool:
        """ Verifies that a given bearer token is valid and retrieves metadata about the token, including the client_id
        used to create the token, expiration timestamp, and scopes granted to the token.

        Returns:
            bool: True if the token is valid, False otherwise
        """
        return self.post(token_validation, self.region, self.oauth.token, locale=locale).status_code == 200


    def get(self, api_endpoint: Callable, category_name: str, *args, **kwargs) -> Optional[bytes]:
        """ Retrieves data from the API endpoint via HTTP GET or cache

        Args:
            api_endpoint (function): API endpoint function from the respective submodule
            category_name (str): category name,
            *args: list of positional arguments for the api endpoint function
            **kwargs: dict of keyword arguments for the api endpoint function

        Returns:
            bytes: data returned from the API endpoint
        """

        if self.cache:
            if self.cache.check(slugify(category_name), *args, **kwargs):
                return self.cache.select(slugify(category_name), *args, **kwargs)

        url, params, data = api_endpoint(self.region, *args, **kwargs)

        for _ in range(5):
            try:
                response = self.oauth.get(url, auth=(self.client_id, self.client_secret), params=params, data=data)
                response.raise_for_status()
            except HTTPError as error:
                if error.response.status_code == 429:
                    sleep(1)
                    continue
            else:
                if response.status_code == 200:
                    if self.cache:
                        if self.cache.chunk_size > 0:
                            self.cache.upsert(slugify(category_name), *args, data=response.content, **kwargs)

                    return response.content
        return None

    def post(self, api_endpoint,  *args, **kwargs):
        """Conveneince function for POST requests"""

        url, params, data = api_endpoint(self.region, *args, **kwargs)
        for _ in range(5):
            try:
                response = self.oauth.post(url, auth=(self.client_id, self.client_secret),
                                           params=params, data=data)
                response.raise_for_status()
            except HTTPError as error:
                if error.response.status_code == 429:
                    sleep(1)
                    continue
            else:
                if response.status_code == 200:
                    return response.content
        else:
            return None

    def add_cache(self, cache):
        """ Initializes connection for cache

        Args:
            cache (str): URI for the cache system
        """
        self.cache = cache

    def close_cache(self):
        if self.cache:
            del self.cache