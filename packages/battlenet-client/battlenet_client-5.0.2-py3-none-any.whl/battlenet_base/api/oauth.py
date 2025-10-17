"""Defines the functions that generate the URLs, parameter lists, and headers
for the OAuth API Endpoints

Functions:
    user_info(region_tag, locale)
    validate_token(region_tag, token, locale)

Misc Variables:
    __version__
    __author__

Author: David "Gahd" Couples
License: GPL v3
Copyright: February 24, 2022
"""

from typing import Optional

from ..utils.decorators import verify_region
from ..utils.utils import auth_host, localize

__version__ = "1.0.3"
__author__ = "David \"Gahd\" Couples"


@verify_region
def authorization(region_tag: str, client_id: str, redirect_uri: str, scope: str,
                  state: str, response_type: Optional[str]="code") -> tuple[str, dict, dict]:
    """Required for authorization code flow

    Args:
        state (str): value suppplied to maintain state between request and callback
        scope (str): list of scopes to authorize
        redirect_uri (str): callback url
        client_id (str): client id provided by API access
        region_tag (str): region of the data request
        response_type (str, optional): response type (typically `code`)

    Returns:
        tuple(str, dict): returns the tuple of url, data, and params
    """
    url = f"{auth_host(region_tag)}/authorize"

    data = {"response_type": response_type, "client_id": client_id, "redirect_uri": redirect_uri, "scope": scope,
            "state": state}

    return url, {}, data


@verify_region
def fetch_token(region_tag: str, grant_type: str, client_id:str, *, code: Optional[str]=None,
          redirect_uri: Optional[str]=None) -> tuple[str, dict, dict]:
    """ Retrieves the token from a authorization code flow

    Args:
        region_tag (str): region of the data request
        grant_type (str): grant type , typically `authorization_code`
        code (str): authorization code received from the authorization server
        redirect_uri (str): return URL, needs to match the original request
        client_id (str): client id provided by API access

    Returns:
        tuple(str, dict, dict): the url, params, and data for retrieving the token
    """
    url = f"{auth_host(region_tag)}/token"

    data = {"grant_type": grant_type}

    if grant_type != "client_credentials":
        data["code"] = code
        data["client_id"] = client_id
        data["redirect_uri"] = redirect_uri

    return url, {}, data


@verify_region
def user_info(region_tag: str, locale: Optional[str] = None) -> tuple[str, dict, dict]:
    """Returns the user info

    Args:
        region_tag (str): region_tag abbreviation
        locale (str): which locale to use for the request

    Returns:
        tuple: The URL (str) and parameters (dict)
    """
    url = f"{auth_host(region_tag)}/userinfo"

    params = {"locale": localize(locale)}

    return url, params, {}


@verify_region
def token_validation(region_tag: str,  token: str, locale: Optional[str] = None) -> tuple[str, dict, dict]:
    """Returns if the token is still valid or not

    Args:
        region_tag (str): region_tag abbreviation
        token (str): token string to validate
        locale (str): which locale to use for the request

    Returns:
        tuple: The URL (str) and parameters (dict)
    """
    url = f"{auth_host(region_tag)}/check_token"

    params = {"locale": localize(locale)}
    data = {'token': token}

    return url, params, data
