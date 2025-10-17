import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from collections.abc import Callable
from typing import Optional, Type
from time import sleep
from urllib.parse import quote_plus
from json import loads
from secrets import token_urlsafe


from .cache.base import BaseCache
from .api import oauth
from .utils.utils import auth_host, api_host, slugify


class BattlenetClient:
    """ Creates a client to access the Battle.net REST API

    Attributes:
        oauth (:obj: `Oauth2Session`): the OAuth session to be used
        state (str, optional): saves the state for client verification
        region (str): the abbreviation of the region
        client_id (str): Client ID for use with the API
        client_secret (str): Client secret for use with the API
        redirect_uri (str, optional): Redirect URI for use with the API
        cache (:obj: `BaseCache`, optional): the cache to use
        config_endpoint (str, optional): endpoint to use for configuration when using OpenID Connection
        jwks (str, optional): endpoint to the JWKS keys
        token (dict): token used for authentication to API
    """
    oauth = None
    state = None
    region = None
    client_id = None
    client_secret = None
    redirect_uri = None
    cache = None
    config_endpoint = None
    jwks = None
    token = None

    def __init__(self, region: str, oauth_session: OAuth2Session, cache = Optional[Type[BaseCache]]):
        self.region = region
        self.oauth = oauth_session
        self.cache = cache
        self.auth_host = auth_host(self.region)
        self.api_host = api_host(self.region)

        if self.grant_type == 'client_credentials':
            self.fetch_token()

    @classmethod
    def authorization_code(cls, region, client_id: str, client_secret: str, redirect_uri: str, scope: list[str], *,
                           auto_refresh_url: Optional[str] = None, auto_refresh_kwargs: Optional[dict] = None,
                           updater: Callable[[dict], None] = None, cache: Optional[BaseCache] = None, ):
        """ Creates an instance of `Battlenet Client` using the Authorization Code Grant, or the Web Application Flow

        Args:
            region (str): The region where the client is connected
            client_id (str): Client ID issued by develop.battle.net
            client_secret (str): Client secret issued by develop.battle.net
            redirect_uri (str): URL to send to authorization service to return
            scope (list of str): list of scopes to grant
            auto_refresh_url (str, optional): Auto-refresh URL when token expires
            auto_refresh_kwargs (dict, optional): Extra arguments passed to OAuth2Session for automatic token refresh
            updater (function, optional): the function to perform the automatic update
            cache (:obj:`BaseCache`, optional): the cache to use

        Returns:
            :obj:`BattlenetClient` configured for Authorization Code Grant, or the Web Application Flow
        """
        cls.client_id = quote_plus(client_id)
        cls.client_secret = quote_plus(client_secret)
        cls.scope = ' '.join(scope)

        cls.grant_type = 'authorization_code'

        cls.redirect_uri = redirect_uri
        updater = updater if updater else cls.token_updater

        oauth_session = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope, auto_refresh_url=auto_refresh_url,
                                      auto_refresh_kwargs=auto_refresh_kwargs, token_updater=updater)
        return cls(region, oauth_session, cache)

    @classmethod
    def client_credential(cls, region: str,  client_id: str, client_secret: str, *,
                          scope: Optional[list[str]] = None, auto_refresh_url: Optional[str] = None,
                          auto_refresh_kwargs: Optional[dict] = None, updater:Optional[Callable]=None,
                          cache = Optional[BaseCache]):
        """ Creates an instance of `Battlenet Client` using the Client Credentials Grant, or the Backend Application
        Flow

        Args:
            region (str): The region where the client is connected
            client_id (str): Client ID issued by develop.battle.net
            client_secret (str): Client secret issued by develop.battle.net
            scope (str): The scope of the request
            auto_refresh_url (str, optional): Auto-refresh URL when token expires
            auto_refresh_kwargs (dict, optional): Extra arguments passed to OAuth2Session for automatic token refresh
            updater (function, optional): specify the function to call when update to the token is required
            cache (:obj:`BaseCache`): cache system

        Returns:
            :obj: `BattlenetClient` configured for client credentials grant oauth2 session
        """
        cls.client_id = quote_plus(client_id)
        cls.client_secret = quote_plus(client_secret)
        cls.grant_type = 'client_credentials'

        cls.scope = " ".join(scope) if scope else None

        updater = cls.token_updater if updater is None else updater

        oauth_session = OAuth2Session(client=BackendApplicationClient(client_id=client_id),
                                      auto_refresh_url=auto_refresh_url,
                                      auto_refresh_kwargs=auto_refresh_kwargs,
                                      token_updater=updater)

        return cls(region, oauth_session, cache)

    @classmethod
    def open_id(cls, region, client_id: str, client_secret: str, redirect_uri: str, scope: list[str], *,
                           auto_refresh_url: Optional[str] = None, auto_refresh_kwargs: Optional[dict] = None,
                           updater: Callable[[dict], None] = None, cache: Optional[BaseCache] = None):
        """ Creates an instance of `Battlenet Client` using Open ID Connect

        Args:
            region (str): The region where the client is connected
            client_id (str): Client ID issued by develop.battle.net
            client_secret (str): Client secret issued by develop.battle.net
            redirect_uri (str): URL to send to authorization service to return
            scope (list of str): list of scopes to grant
            auto_refresh_url (str, optional): Auto-refresh URL when token expires
            auto_refresh_kwargs (dict, optional): Extra arguments passed to OAuth2Session for automatic token refresh
            updater (callable, optional): the function to perform the automatic update
            cache (:obj:`BaseCache`): cache system

        Returns:
            :obj:`BattlenetClient` configured for authorization code grant oauth2 session using Open ID Connect
        """
        cls.scope = scope.append("openid")
        cls.config_endpoint = f"{auth_host(region)}/.well-known/openid-configuration"
        cls.jwks = f"{auth_host(region)}/jwks/certs"

        return cls.authorization_code(region, client_id, client_secret, redirect_uri, scope,
                                      auto_refresh_url=auto_refresh_url, auto_refresh_kwargs=auto_refresh_kwargs,
                                      updater=updater, cache=cache)

    def get_authorization_url(self) -> str:
        """ Returns the authorization URL for authorization Authorization Code Grant, or the Web Application Flow

        Returns:
          str: authorization url
        """
        self.state = token_urlsafe(64)
        return oauth.authorization(self.region, self.client_id, self.redirect_uri, self.scope, self.state)

    def callback(self, code: str, state: str) -> bool:
        """ Processes the callback response from the authorization code grant.

        Args:
            code (str): code provided during the callback request
            state (str): state provided by the callback request
        """
        if state == self.state:
            self.fetch_token(code)
            return True

        return False

    def token_updater(self, token: dict):
        """ Updates the token data provided by `token`

        Args:
            token (dict): token returned from authorization server
        """
        if token:
            self.token = token


    def fetch_token(self, code: Optional[str]=None) -> None:
        """ Fetches the token from the authorization server

        Args
            code (str, optional): authorization code provided by authorization server
        """

        token = self.post(oauth.fetch_token,self.grant_type, redirect_uri=self.redirect_uri, code=code)

        if token:
            self.token_updater(loads(token))

    def is_token_valid(self) -> bool:
        """ Verifies that a given bearer token is valid and retrieves metadata about the token, including the client_id
        used to create the token, expiration timestamp, and scopes granted to the token.

        Returns:
            bool: True if the token is valid, False otherwise
        """
        return self.post(oauth.token_validation, self.oauth.access_token) is not None

    def get_user_info(self) -> Optional[dict]:
        """ Retrieves user info from the authorization server

        Returns:
            dict: user info
        """
        return self.get(oauth.user_info, "no-cache", self.oauth.access_token)

    def get(self, api_endpoint: Callable, category_name: str, *args, **kwargs) -> Optional[bytes]:
        """ Retrieves data from the API endpoint via HTTP GET or cache

        Args:
            api_endpoint (function): API endpoint function from the respective submodule
            category_name (str): category name from the respective submodule
            *args: list of positional arguments for the api endpoint function
            **kwargs: dict of keyword arguments for the api endpoint function

        Returns:
            bytes: data returned from the API endpoint if successful
            None: on failure
        """

        if self.cache:
            if self.cache.check(slugify(category_name), *args, **kwargs):
                return self.cache.select(slugify(category_name), *args, **kwargs)

        url, params, data, headers = api_endpoint(self.region, *args, **kwargs)

        if self.token:
            headers["Authorization"] = f"Bearer {self.token["access_token"]}"

        for _ in range(5):
            try:
                response = requests.get(url, auth=(self.client_id, self.client_secret), params=params, data=data,
                                        headers=headers)
                response.raise_for_status()
            except requests.HTTPError as error:
                if error.response.status_code == 429:
                    sleep(1)
                    continue
                if error.response.status_code in (400, 401):
                    return None
            else:
                if response.status_code == 200:
                    if self.cache:
                        self.cache.upsert(slugify(category_name), *args, data=response.content, **kwargs)

                    return response.content
        return None

    def post(self, api_endpoint,  *args, **kwargs) -> Optional[bytes]:
        """ Retrieves data from the API endpoint via HTTP GET or cache

        Args:
            api_endpoint (function): API endpoint function from the respective submodule
            *args: list of positional arguments for the api endpoint function
            **kwargs: dict of keyword arguments for the api endpoint function

        Returns:
            bytes: data returned from the API endpoint if successful
            None: on failure
        """

        url, params, data, headers = api_endpoint(self.region, *args, **kwargs)

        if self.token:
            headers["Authorization"] = f"Bearer {self.token["access_token"]}"

        for _ in range(5):
            try:
                response = requests.post(url, auth=(self.client_id, self.client_secret),
                                           params=params, data=data, headers=headers)
                response.raise_for_status()
            except requests.HTTPError as error:
                if error.response.status_code == 429:
                    sleep(1)
                    continue
                if error.response.status_code in (400, 401):
                    return None
            else:
                if response.status_code == 200:
                    return response.content
        else:
            return None

    def add_cache(self, cache):
        """ Associates the provided cache with the client

        Args:
            cache (:obj:`BaseCache`): cache system
        """
        self.cache = cache

    def close_cache(self):
        """ Closes the client assoicated cache """
        if self.cache:
            del self.cache